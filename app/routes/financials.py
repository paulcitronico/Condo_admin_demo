from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from sqlalchemy import func, extract
from app import db
from app.models.financial import FinancialAccount, FinancialTransaction, ServicePayment
from app.models.user import User
from app.routes.roles import require_permission

bp = Blueprint('financials', __name__, url_prefix='/financials')


@bp.route('/')
@login_required
@require_permission('financials', level=1)
def index():
    stats = get_financial_overview()
    # FIX: Cuentas críticas - ahora buscamos balance > 0 (deuda real)
    critical_accounts = FinancialAccount.query.filter(
        FinancialAccount.status.in_(['critical', 'overdue'])
    ).order_by(
        (FinancialAccount.total_owed - FinancialAccount.total_paid).desc()
    ).limit(5).all()
    
    pending_services = ServicePayment.query.filter_by(
        status='pending'
    ).order_by(ServicePayment.due_date).limit(5).all()
    
    recent_transactions = FinancialTransaction.query.order_by(
        FinancialTransaction.created_at.desc()
    ).limit(10).all()

    return render_template('financials/index.html',
                           stats=stats,
                           critical_accounts=critical_accounts,
                           pending_services=pending_services,
                           recent_transactions=recent_transactions,
                           now=datetime.now())


@bp.route('/accounts')
@login_required
@require_permission('financials', level=1)
def accounts():
    """Lista de todas las cuentas"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')

    query = FinancialAccount.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    accounts = query.order_by(FinancialAccount.unit_number).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template('financials/accounts.html', accounts=accounts)


@bp.route('/account/<int:account_id>')
@login_required
@require_permission('financials', level=1)
def account_detail(account_id):
    """Detalle de cuenta con historial"""
    account = FinancialAccount.query.get_or_404(account_id)

    page = request.args.get('page', 1, type=int)
    transactions = account.transactions.paginate(page=page, per_page=20, error_out=False)

    return render_template('financials/account_detail.html',
                           account=account,
                           transactions=transactions)


@bp.route('/transaction/add', methods=['GET', 'POST'])
@login_required
@require_permission('financials', level=2)
def add_transaction():
    if request.method == 'POST':
        try:
            # Obtener y validar datos del formulario
            account_id = request.form.get('account_id', type=int)
            amount_str = request.form.get('amount', type=str)
            transaction_type = request.form.get('transaction_type')
            category = request.form.get('category', 'other')

            # Validaciones básicas
            if not account_id or not amount_str or not transaction_type:
                flash('Faltan campos requeridos', 'danger')
                return redirect(url_for('financials.add_transaction'))

            # FIX: convertir string → Decimal de inmediato
            try:
                amount_decimal = Decimal(amount_str)
            except InvalidOperation:
                flash('El monto ingresado no es válido', 'danger')
                return redirect(url_for('financials.add_transaction'))

            if amount_decimal <= Decimal('0'):
                flash('El monto debe ser mayor a cero', 'danger')
                return redirect(url_for('financials.add_transaction'))

            # Crear la transacción
            new_trans = FinancialTransaction(
                account_id=account_id,
                amount=amount_decimal,
                transaction_type=transaction_type,
                category=category,
                description=request.form.get('description', ''),
                period_month=request.form.get('period_month', type=int) or datetime.now().month,
                period_year=request.form.get('period_year', type=int) or datetime.now().year,
                transaction_date=datetime.now().date(),
                reference_number=request.form.get('reference_number', ''),
                status='completed',
                created_by_id=current_user.id,
                created_at=datetime.now()
            )

            # Añadir transacción
            db.session.add(new_trans)

            # Actualizar balance de la cuenta
            account = FinancialAccount.query.get_or_404(account_id)
            account.update_balance()

            db.session.commit()
            flash('Transacción registrada correctamente', 'success')

            # Si es un pago, redirigir a la boleta para imprimir
            if transaction_type == 'payment':
                return redirect(url_for('financials.view_receipt', transaction_id=new_trans.id))

            return redirect(url_for('financials.account_detail', account_id=account_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar transacción: {str(e)}', 'danger')
            return redirect(url_for('financials.add_transaction'))

    # GET request: mostrar el formulario
    accounts = FinancialAccount.query.all()
    selected_account_id = request.args.get('account_id', 0, type=int)

    return render_template('financials/add_transaction.html',
                           accounts=accounts,
                           now=datetime.now(),
                           selected_account_id=selected_account_id)


@bp.route('/services')
@login_required
@require_permission('financials', level=1)
def services():
    """Lista de pagos de servicios del edificio con filtros dinámicos"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    category_filter = request.args.get('category', 'all')
    month_filter = request.args.get('month', 'all')

    query = ServicePayment.query
    today = date.today()

    # Filtro de Categoría (que faltaba en tu lógica de Python)
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)

    # Lógica de Estado dinámica
    if status_filter == 'pending':
        # Solo los que están pendientes Y aún no vencen
        query = query.filter(ServicePayment.status == 'pending', ServicePayment.due_date >= today)
    elif status_filter == 'overdue':
        # El caso que mencionaste: Pendientes cuya fecha ya pasó
        query = query.filter(ServicePayment.status == 'pending', ServicePayment.due_date < today)
    elif status_filter == 'paid':
        query = query.filter_by(status='paid')

    # Filtro por Mes de vencimiento
    if month_filter != 'all':
        query = query.filter(extract('month', ServicePayment.due_date) == int(month_filter))

    services = query.order_by(ServicePayment.due_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )

    # Pasamos 'today' al template para el marcado visual en la tabla
    return render_template('financials/services.html', 
                           services=services, 
                           today=today)


@bp.route('/service/add', methods=['GET', 'POST'])
@login_required
@require_permission('financials', level=2)
def add_service():
    """Registrar pago de servicio"""
    if request.method == 'POST':
        # FIX: leer el monto como string y convertir a Decimal
        amount_str = request.form.get('amount', '')
        try:
            amount_decimal = Decimal(amount_str)
        except (InvalidOperation, ValueError):
            flash('El monto ingresado no es válido', 'danger')
            return redirect(url_for('financials.add_service'))

        service = ServicePayment(
            service_name=request.form.get('service_name'),
            provider=request.form.get('provider'),
            amount=amount_decimal,
            category=request.form.get('category'),
            due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date(),
            invoice_number=request.form.get('invoice_number'),
            notes=request.form.get('notes'),
            status='pending'
        )

        db.session.add(service)
        db.session.commit()

        flash('Servicio registrado exitosamente', 'success')
        return redirect(url_for('financials.services'))

    return render_template('financials/add_service.html')


@bp.route('/service/<int:service_id>')
@login_required
@require_permission('financials', level=1)
def service_detail(service_id):
    """Muestra el detalle del servicio y permite registrar pagos por residente"""
    service = ServicePayment.query.get_or_404(service_id)

    # Obtener todas las cuentas para listarlas y ver quién ya pagó
    accounts = FinancialAccount.query.order_by(FinancialAccount.unit_number).all()

    # Identificar qué cuentas ya tienen una transacción de pago vinculada a este servicio
    paid_accounts_ids = [
        t.account_id for t in service.resident_transactions
        if t.transaction_type == 'payment'
    ]

    return render_template('financials/service_detail.html',
                           service=service,
                           accounts=accounts,
                           paid_accounts_ids=paid_accounts_ids)


@bp.route('/service/<int:service_id>/mark_paid_provider', methods=['POST'])
@login_required
@require_permission('financials', level=2)
def mark_service_paid_provider(service_id):
    """Marca que el CONDOMINIO le pagó al PROVEEDOR (Ej: Prosegur)"""
    service = ServicePayment.query.get_or_404(service_id)
    service.status = 'paid'
    service.paid_date = datetime.now().date()
    db.session.commit()

    flash(f'El servicio a {service.provider} ha sido marcado como pagado por el condominio.', 'success')
    return redirect(url_for('financials.service_detail', service_id=service.id))

#nueva ruta de pago directo desde la tabla de servicios
@bp.route('/service/<int:service_id>/mark-paid', methods=['POST'])
@login_required
@require_permission('financials', level=2)
def mark_service_paid(service_id):
    """Marca un servicio como pagado directamente desde la tabla"""
    service = ServicePayment.query.get_or_404(service_id)
    
    # Verificar que el servicio esté pendiente
    if service.status != 'pending':
        flash('Este servicio ya está pagado o tiene otro estado', 'warning')
        return redirect(url_for('financials.services'))
    
    # Marcar como pagado
    service.status = 'paid'
    service.paid_date = datetime.now().date()
    
    try:
        db.session.commit()
        flash(f'✅ Servicio "{service.service_name}" marcado como pagado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al marcar el servicio como pagado: {str(e)}', 'danger')
    
    return redirect(url_for('financials.services'))

@bp.route('/service/<int:service_id>/pay_resident/<int:account_id>', methods=['POST'])
@login_required
@require_permission('financials', level=2)
def register_resident_service_payment(service_id, account_id):
    """Registra que un RESIDENTE pagó su cuota de este servicio extraordinario"""
    service = ServicePayment.query.get_or_404(service_id)
    account = FinancialAccount.query.get_or_404(account_id)

    # FIX: leer como string y convertir a Decimal de inmediato
    amount_str = request.form.get('amount', '')
    try:
        amount_decimal = Decimal(amount_str)
    except (InvalidOperation, ValueError):
        flash('Monto inválido. Ingrese un número válido.', 'danger')
        return redirect(url_for('financials.service_detail', service_id=service.id))

    if amount_decimal <= Decimal('0'):
        flash('Monto inválido. Debe ser mayor a 0.', 'danger')
        return redirect(url_for('financials.service_detail', service_id=service.id))

    # Crear el recibo de pago (Transacción)
    payment = FinancialTransaction(
        account_id=account.id,
        transaction_type='payment',
        amount=amount_decimal,
        category=service.category,
        service_payment_id=service.id,  # <-- Enlace clave
        description=f"Pago cuota extraordinaria: {service.service_name}",
        period_month=datetime.now().month,
        period_year=datetime.now().year,
        transaction_date=datetime.now().date(),
        status='completed',
        created_by_id=current_user.id
    )

    db.session.add(payment)
    account.update_balance()
    db.session.commit()

    flash(f'Pago registrado exitosamente para la unidad {account.unit_number}.', 'success')
    # Generamos la boleta de inmediato
    return redirect(url_for('financials.view_receipt', transaction_id=payment.id))


@bp.route('/receipt/<int:transaction_id>')
@login_required
@require_permission('financials', level=1)
def view_receipt(transaction_id):
    """Genera la boleta (recibo) de un pago específico"""
    transaction = FinancialTransaction.query.get_or_404(transaction_id)

    if transaction.transaction_type != 'payment':
        flash('Las boletas solo se generan para transacciones de tipo "Pago".', 'danger')
        return redirect(url_for('financials.index'))

    return render_template('financials/boleta.html',
                           transaction=transaction,
                           now=datetime.now())


@bp.route('/voucher/<int:transaction_id>')
@login_required
@require_permission('financials', level=1)
def view_voucher(transaction_id):
    """Genera el comprobante de un cargo o ajuste"""
    transaction = FinancialTransaction.query.get_or_404(transaction_id)

    if transaction.transaction_type not in ('charge', 'adjustment'):
        flash('Los comprobantes solo se generan para cargos y ajustes.', 'danger')
        return redirect(url_for('financials.index'))

    return render_template('financials/voucher.html',
                           transaction=transaction,
                           now=datetime.now())


def get_financial_overview():
    """Calcula estadísticas financieras del condominio"""
    # FIX: Suma absolutamente todos los pagos de tipo 'payment'
    total_collected = db.session.query(
        func.sum(FinancialTransaction.amount)
    ).filter(
        FinancialTransaction.transaction_type == 'payment'
    ).scalar() or Decimal('0.00')

    # FIX: Deuda total - solo sumamos balances positivos (deuda real)
    # owed - paid = deuda (positivo) o crédito (negativo)
    total_balance = db.session.query(
        func.sum(FinancialAccount.total_owed - FinancialAccount.total_paid)
    ).scalar() or Decimal('0.00')
    
    # Si el balance total es negativo, significa que hay más créditos que deudas
    # Mostramos 0 en ese caso, o el valor positivo si hay deuda real
    outstanding_debts = max(Decimal('0.00'), total_balance)

    total_units = FinancialAccount.query.count()
    
    # FIX: Unidades al día = las que no tienen deuda (balance <= 0)
    current_units = FinancialAccount.query.filter(
        FinancialAccount.total_owed <= FinancialAccount.total_paid
    ).count()
    
    collection_rate = 0 if total_units == 0 else (current_units / total_units * 100)

    return {
        'total_collected': float(Decimal(str(total_collected))),
        'outstanding_debts': float(Decimal(str(outstanding_debts))),
        'collection_rate': collection_rate
    }


@bp.route('/account/create', methods=['GET', 'POST'])
@login_required
@require_permission('financials', level=2)
def create_account():
    if request.method == 'POST':
        unit = request.form.get('unit_number')
        user_id = request.form.get('user_id') or None

        # Validar si ya existe
        if FinancialAccount.query.filter_by(unit_number=unit).first():
            flash('Esa unidad ya tiene una cuenta financiera.', 'danger')
            return redirect(url_for('financials.create_account'))

        new_account = FinancialAccount(unit_number=unit, user_id=user_id)
        db.session.add(new_account)
        db.session.commit()
        flash(f'Unidad {unit} creada exitosamente.', 'success')
        return redirect(url_for('financials.accounts'))

    # Para el dropdown de usuarios
    from app.models.user import User
    users = User.query.all()
    return render_template('financials/create_account.html', users=users)


@bp.route('/sync-accounts')
@login_required
@require_permission('financials', level=2)
def sync_accounts():
    from app.models.user import User
    users = User.query.filter(User.unit_number != None).all()
    created = 0
    for u in users:
        if not FinancialAccount.query.filter_by(unit_number=u.unit_number).first():
            acc = FinancialAccount(unit_number=u.unit_number, user_id=u.id)
            db.session.add(acc)
            created += 1
    db.session.commit()
    flash(f'Sincronización lista: {created} cuentas creadas.', 'success')
    return redirect(url_for('financials.accounts'))


@bp.route('/recalculate-balances')
@login_required
@require_permission('financials', level=2)
def recalculate_balances():
    """Recalcula todos los balances (para corregir inconsistencias)"""
    try:
        accounts = FinancialAccount.query.all()
        for account in accounts:
            account.update_balance()
        db.session.commit()
        flash(f'Balances recalculados para {len(accounts)} cuentas', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al recalcular balances: {str(e)}', 'danger')

    return redirect(url_for('financials.accounts'))