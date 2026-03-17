# app/models/logistica.py
from datetime import datetime
from app import db

class Visita(db.Model):
    __tablename__ = 'visitas'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    rut = db.Column(db.String(12), nullable=False)
    depto_visitado = db.Column(db.String(10), nullable=False)
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)

class Paqueteria(db.Model):
    __tablename__ = 'paqueteria'
    id = db.Column(db.Integer, primary_key=True)
    proveedor_paquete = db.Column(db.String(100), nullable=False)
    destinatario = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50)) # Frágil, No frágil, Manejar con cuidado
    persona_retira = db.Column(db.String(100))
    firma = db.Column(db.Text) # Almacenado como Base64
    hora_llegada = db.Column(db.DateTime, default=datetime.utcnow)
    hora_retiro = db.Column(db.DateTime, nullable=True)