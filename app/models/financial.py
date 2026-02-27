from datetime import datetime
from decimal import Decimal
from app import db


class FinancialAccount(db.Model):
    """Modelo de Cuentas por Unidad/Departamento"""
    __tablename__ = 'financial_accounts'

    id = db.Column(db.Integer, primary_key=True)

    # Unidad
    unit_number = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Propietario/Residente
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', backref=db.backref('financial_account', uselist=False))

    # Balance  ── FIX: defaults explícitos con Decimal
    total_owed = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))  # Total adeudado
    total_paid = db.Column(db.Numeric(10, 2), default=Decimal('0.00'))  # Total pagado

    # Estado: current, overdue, critical
    status = db.Column(db.String(20), default='current', index=True)
    months_overdue = db.Column(db.Integer, default=0)

    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con transacciones
    transactions = db.relationship(
        'FinancialTransaction', backref='account', lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='FinancialTransaction.created_at.desc()'
    )

    @property
    def balance(self):
        """Balance actual (negativo = deuda, positivo = a favor).
        Retorna Decimal para mantener precisión monetaria."""
        # FIX: convertir ambos campos a Decimal antes de operar
        paid = Decimal(str(self.total_paid)) if self.total_paid is not None else Decimal('0.00')
        owed = Decimal(str(self.total_owed)) if self.total_owed is not None else Decimal('0.00')
        return paid - owed

    def update_balance(self):
        """Actualiza el balance basado en transacciones completadas"""
        # Usar las relaciones para calcular de forma más eficiente
        completed_transactions = self.transactions.filter_by(status='completed')

        # Calcular totales desde las transacciones
        total_owed = Decimal('0.00')
        total_paid = Decimal('0.00')

        for trans in completed_transactions:
            # FIX: conversión explícita de cada monto a Decimal(str(...))
            amount = Decimal(str(trans.amount)) if trans.amount is not None else Decimal('0.00')

            if trans.transaction_type == 'charge':
                total_owed += amount
            elif trans.transaction_type == 'payment':
                total_paid += amount
            elif trans.transaction_type == 'adjustment':
                # Ajustes: positivos suman a pagado, negativos suman a adeudado
                if amount > Decimal('0.00'):
                    total_paid += amount
                else:
                    total_owed += abs(amount)

        self.total_owed = total_owed
        self.total_paid = total_paid

        # Actualizar estado basado en el balance
        # FIX: self.balance ya retorna Decimal, comparar con Decimal
        balance = self.balance
        if balance < Decimal('0.00'):
            debt_amount = abs(balance)
            if debt_amount > Decimal('1000.00'):  # Deuda crítica > $1000
                self.status = 'critical'
            else:
                self.status = 'overdue'
            # Calcular meses de atraso (simplificado)
            self.months_overdue = max(1, self.months_overdue)
        else:
            self.status = 'current'
            self.months_overdue = 0

        self.updated_at = datetime.utcnow()
        return True

    def __repr__(self):
        return f'<FinancialAccount Unit:{self.unit_number}>'


class FinancialTransaction(db.Model):
    """Modelo de Transacciones Financieras"""
    __tablename__ = 'financial_transactions'

    id = db.Column(db.Integer, primary_key=True)

    account_id = db.Column(db.Integer, db.ForeignKey('financial_accounts.id'), nullable=False)

    # NUEVO: Relación opcional con un Servicio del Edificio (para cuotas extraordinarias)
    service_payment_id = db.Column(db.Integer, db.ForeignKey('service_payments.id'), nullable=True)
    service_payment = db.relationship(
        'ServicePayment',
        backref=db.backref('resident_transactions', lazy='dynamic')
    )

    # Tipo: charge (cargo), payment (pago), adjustment (ajuste)
    transaction_type = db.Column(db.String(20), nullable=False, index=True)

    # Monto  ── FIX: Numeric(10,2) sin default float
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    # Categoría: common_expenses, water, electricity, maintenance, other
    category = db.Column(db.String(50), nullable=False, index=True)

    # Detalles
    description = db.Column(db.Text)
    reference_number = db.Column(db.String(50))  # Número de factura/recibo

    # Fecha de transacción (puede ser diferente a created_at)
    transaction_date = db.Column(db.Date, nullable=False, index=True)

    # Período al que corresponde (mes/año)
    period_month = db.Column(db.Integer)
    period_year = db.Column(db.Integer)

    # Estado: pending, completed, cancelled
    status = db.Column(db.String(20), default='completed', index=True)

    # Usuario que registró la transacción
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.transaction_type} ${self.amount}>'


class ServicePayment(db.Model):
    """Modelo de Pagos de Servicios del Edificio"""
    __tablename__ = 'service_payments'

    id = db.Column(db.Integer, primary_key=True)

    # Servicio
    service_name = db.Column(db.String(100), nullable=False)
    provider = db.Column(db.String(100))

    # Monto  ── Numeric(10,2), sin default float
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    # Categoría: electricity, water, maintenance, security, other
    category = db.Column(db.String(50), nullable=False, index=True)

    # Fechas
    due_date = db.Column(db.Date, nullable=False, index=True)
    paid_date = db.Column(db.Date)

    # Estado: pending, paid, overdue
    status = db.Column(db.String(20), default='pending', index=True)

    # Referencia
    invoice_number = db.Column(db.String(50))
    payment_reference = db.Column(db.String(50))

    # Notas
    notes = db.Column(db.Text)

    # Usuario que registró el pago
    paid_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    paid_by = db.relationship('User')

    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ServicePayment {self.service_name} ${self.amount}>'