# app/models/paqueteria.py
from datetime import datetime
from app import db
from app.models.user import User

class Paqueteria(db.Model):
    __tablename__ = 'paqueteria'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Datos de llegada
    proveedor_paquete = db.Column(db.String(100), nullable=False) # ej: Chilexpress, Starken
    destinatario = db.Column(db.String(100), nullable=False)      # Nombre o depto
    tipo = db.Column(db.String(50))                               # Frágil, No frágil, Manejar con cuidado
    hora_llegada = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Datos de retiro
    persona_retira = db.Column(db.String(100), nullable=True)
    firma = db.Column(db.Text, nullable=True)                     # Aquí guardaremos la firma en Base64
    hora_retiro = db.Column(db.DateTime, nullable=True)
    
    # Trazabilidad (Opcional pero recomendado: saber qué guardia lo recibió y cuál lo entregó)
    recibido_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    entregado_por_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    recibido_por = db.relationship('User', foreign_keys=[recibido_por_id])
    entregado_por = db.relationship('User', foreign_keys=[entregado_por_id])

    @property
    def estado(self):
        """Retorna 'Pendiente' si no tiene hora de retiro, o 'Entregado' si ya se retiró."""
        return 'Entregado' if self.hora_retiro else 'Pendiente'