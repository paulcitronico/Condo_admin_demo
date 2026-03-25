from datetime import datetime
from .. import db 

class Comprobante(db.Model):
    __tablename__ = 'comprobantes'
    
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    # Fecha seleccionada por el usuario
    payment_date = db.Column(db.Date, nullable=False)
    # Fecha de registro automática del sistema
    created_at = db.Column(db.DateTime, default=datetime.now)
    filename = db.Column(db.String(255), nullable=False)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('comprobantes', lazy=True))

    def __repr__(self):
        return f'<Comprobante {self.amount}>'