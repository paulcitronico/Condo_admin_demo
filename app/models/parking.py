from datetime import datetime
from app import db


class ParkingSpot(db.Model):
    """Modelo de Espacio de Estacionamiento"""
    __tablename__ = 'parking_spots'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificación
    spot_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    floor = db.Column(db.String(20), nullable=False)  # P1, P2, etc.
    sector = db.Column(db.String(50))  # Sector A, B, etc.
    
    # Tipo: regular, disabled, visitor, reserved, ev_charging
    spot_type = db.Column(db.String(20), default='regular', index=True)
    
    # Estado: available, occupied, reserved, maintenance
    status = db.Column(db.String(20), default='available', index=True)
    
    # Asignación
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_user = db.relationship('User', backref=db.backref('parking_spots', lazy='dynamic'))
    
    # Detalles del vehículo asignado
    vehicle_plate = db.Column(db.String(20))
    vehicle_make = db.Column(db.String(50))
    vehicle_model = db.Column(db.String(50))
    vehicle_color = db.Column(db.String(30))
    
    # Notas
    notes = db.Column(db.Text)
    
    # Auditoría
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Historial de cambios
    logs = db.relationship('ParkingLog', backref='parking_spot', lazy='dynamic',
                          cascade='all, delete-orphan', order_by='ParkingLog.created_at.desc()')
    
    def assign_to_user(self, user, vehicle_data=None):
        """Asigna el espacio a un usuario"""
        self.assigned_user_id = user.id
        self.status = 'occupied'
        
        if vehicle_data:
            self.vehicle_plate = vehicle_data.get('plate')
            self.vehicle_make = vehicle_data.get('make')
            self.vehicle_model = vehicle_data.get('model')
            self.vehicle_color = vehicle_data.get('color')
        
        # Registrar en log
        log = ParkingLog(
            parking_spot_id=self.id,
            action='assigned',
            user_id=user.id,
            details=f'Asignado a {user.full_name}'
        )
        db.session.add(log)
    
    def unassign(self):
        """Libera el espacio"""
        old_user = self.assigned_user
        self.assigned_user_id = None
        self.status = 'available'
        self.vehicle_plate = None
        self.vehicle_make = None
        self.vehicle_model = None
        self.vehicle_color = None
        
        # Registrar en log
        if old_user:
            log = ParkingLog(
                parking_spot_id=self.id,
                action='unassigned',
                user_id=old_user.id,
                details=f'Liberado de {old_user.full_name}'
            )
            db.session.add(log)
    
    @property
    def is_available(self):
        """Verifica si está disponible"""
        return self.status == 'available' and self.is_active
    
    def __repr__(self):
        return f'<ParkingSpot {self.spot_number}>'


class ParkingLog(db.Model):
    """Modelo de Historial de Estacionamientos"""
    __tablename__ = 'parking_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    parking_spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # SE AGREGA foreign_keys=[user_id]
    user = db.relationship('User', foreign_keys=[user_id])
    
    # Tipo de acción: assigned, unassigned, status_change, maintenance
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    
    # Usuario que realizó la acción
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # Esta ya está bien, pero asegúrate que se vea así:
    performed_by = db.relationship('User', foreign_keys=[performed_by_id])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ParkingLog {self.action} - Spot {self.parking_spot_id}>'
