from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func, extract
from app import db
from app.models.financial import FinancialAccount, FinancialTransaction, ServicePayment
from app.routes.roles import require_permission

bp = Blueprint('financials', __name__, url_prefix='/financials')


@bp.route('/')
@login_required
@require_permission('financials', level=1)
def index():
    stats = get_financial_overview()
    critical_accounts = FinancialAccount.query.filter(FinancialAccount.status == 'critical').order_by((FinancialAccount.total_owed - FinancialAccount.total_paid).desc()).limit(5).all()
    pending_services = ServicePayment.query.filter_by(status='pending').order_by(ServicePayment.due_date).limit(5).all()
    recent_transactions = FinancialTransaction.query.order_by(FinancialTransaction.created_at.desc()).limit(10).all()
    
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
            from decimal import Decimal
            
            # Obtener y validar datos del formulario
            account_id = request.form.get('account_id', type=int)
            amount = request.form.get('amount', type=str)
            transaction_type = request.form.get('transaction_type')
            category = request.form.get('category', 'other')
            
            # Validaciones básicas
            if not account_id or not amount or not transaction_type:
                flash('Faltan campos requeridos', 'danger')
                return redirect(url_for('financials.add_transaction'))
            
            # Validar que el monto sea positivo
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
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
    """Lista de pagos de servicios del edificio"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    
    query = ServicePayment.query
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    services = query.order_by(ServicePayment.due_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('financials/services.html', services=services)


@bp.route('/service/add', methods=['GET', 'POST'])
@login_required
@require_permission('financials', level=2)
def add_service():
    """Registrar pago de servicio"""
    if request.method == 'POST':
        service = ServicePayment(
            service_name=request.form.get('service_name'),
            provider=request.form.get('provider'),
            amount=request.form.get('amount', type=float),
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


def get_financial_overview():
    current_month = datetime.now().month
    current_year = datetime.now().year
    total_collected = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.transaction_type == 'payment',
        FinancialTransaction.period_month == current_month,
        FinancialTransaction.period_year == current_year
    ).scalar() or 0
    outstanding = db.session.query(func.sum(FinancialAccount.total_owed - FinancialAccount.total_paid)).scalar() or 0
    total_units = FinancialAccount.query.count()
    collection_rate = 100 if total_units == 0 else (FinancialAccount.query.filter_by(status='current').count() / total_units * 100)
    
    return {
        'total_collected': float(total_collected),
        'outstanding_debts': float(outstanding),
        'collection_rate': collection_rate
    }

@bp.route('/service/<int:service_id>')
@login_required
@require_permission('financials', level=1)
def service_detail(service_id):
    service = ServicePayment.query.get_or_404(service_id)
    return render_template('financials/service_detail.html', service=service)

@bp.route('/account/create', methods=['GET', 'POST'])
@login_required
@require_permission('financials', level=2) # Nivel 2 para crear
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