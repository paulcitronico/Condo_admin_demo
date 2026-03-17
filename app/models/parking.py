# app/models/parking.py
from datetime import datetime
from app import db
from app.models.user import User


class ParkingSpot(db.Model):
    """Modelo de Espacio de Estacionamiento con Coordenadas de Grilla"""
    __tablename__ = 'parking_spots'
    
    id = db.Column(db.Integer, primary_key=True)
    spot_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    floor = db.Column(db.String(20), nullable=False)
    sector = db.Column(db.String(50))
    
    # --- CAMPOS PARA LA GRILLA ---
    row_index = db.Column(db.Integer, default=0)
    col_index = db.Column(db.Integer, default=0)

    spot_type = db.Column(db.String(20), default='regular', index=True)
    status = db.Column(db.String(20), default='available', index=True)
    
    # ═══════════════════════════════════════════════════════
    # ESTADO DE MANTENIMIENTO (NUEVO)
    # ═══════════════════════════════════════════════════════
    under_maintenance = db.Column(db.Boolean, default=False) # Fix para AttributeError

    # ═══════════════════════════════════════════════════════
    # DUEÑO PERMANENTE
    # ═══════════════════════════════════════════════════════
    assigned_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assigned_user = db.relationship(
        'User', 
        foreign_keys=[assigned_user_id],
        backref=db.backref('parking_spots', lazy='dynamic')
    )
    
    # ═══════════════════════════════════════════════════════
    # OCUPANTE ACTUAL (Físico)
    # ═══════════════════════════════════════════════════════
    occupied_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    occupied_by_name = db.Column(db.String(100), nullable=True)
    occupied_at = db.Column(db.DateTime, nullable=True)
    patente_externa = db.Column(db.String(10))
    rut_externo = db.Column(db.String(12))
    
    occupant = db.relationship(
        'User', 
        foreign_keys=[occupied_by_id],
        backref=db.backref('occupying_spots', lazy='dynamic')
    )
    
    # ═══════════════════════════════════════════════════════
    # DATOS DEL VEHÍCULO (Unificados para Dueño y Visita)
    # ═══════════════════════════════════════════════════════
    vehicle_plate = db.Column(db.String(20))
    vehicle_make = db.Column(db.String(50))
    vehicle_model = db.Column(db.String(50))
    vehicle_color = db.Column(db.String(30))
    
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    logs = db.relationship('ParkingLog', backref='parking_spot', lazy='dynamic', cascade='all, delete-orphan')

    # ═══════════════════════════════════════════════════════
    # PROPIEDADES HELPER
    # ═══════════════════════════════════════════════════════
    
    @property
    def has_owner(self):
        return self.assigned_user_id is not None
    
    @property
    def is_physically_occupied(self):
        return self.occupied_by_id is not None or self.occupied_by_name is not None
    
    @property
    def occupant_display_name(self):
        if self.occupied_by_id and self.occupant:
            return self.occupant.full_name
        elif self.occupied_by_name:
            return self.occupied_by_name
        return None
    
    @property
    def visual_state(self):
        """Prioridad de estados: Inactivo -> Mantenimiento -> Ocupación"""
        if not self.is_active:
            return 'gray'
        
        # El morado tiene prioridad sobre los estados de ocupación
        if self.under_maintenance:
            return 'purple'
        
        has_owner = self.has_owner
        is_occupied = self.is_physically_occupied
        
        if has_owner and is_occupied:
            return 'split'     # Azul/Rojo
        elif has_owner and not is_occupied:
            return 'blue'      # Dueño ausente
        elif not has_owner and is_occupied:
            return 'red'       # Visita en espacio libre
        else:
            return 'green'     # Libre
        
    # ═══════════════════════════════════════════════════════
    # MÉTODOS DE ACCIÓN
    # ═══════════════════════════════════════════════════════

    def assign_to_user(self, user, vehicle_data=None):
        self.assigned_user_id = user.id
        self.status = 'assigned'
        if vehicle_data:
            self.vehicle_plate = vehicle_data.get('plate')
            self.vehicle_make = vehicle_data.get('make')
            self.vehicle_model = vehicle_data.get('model')
            self.vehicle_color = vehicle_data.get('color')
        
        db.session.add(ParkingLog(
            parking_spot_id=self.id, action='assigned', user_id=user.id, 
            details=f'Asignado a {user.full_name}'
        ))

    def unassign(self):
        old_user = self.assigned_user
        self.assigned_user_id = None
        self.status = 'available'
        self.vehicle_plate = None
        self.vehicle_make = None
        self.vehicle_model = None
        self.vehicle_color = None
        
        if old_user:
            db.session.add(ParkingLog(
                parking_spot_id=self.id, action='unassigned', user_id=old_user.id, 
                details=f'Liberado de {old_user.full_name}'
            ))

    def occupy(self, occupant_name=None, occupant_user_id=None, performed_by=None, **kwargs):
        """
        Marcar que alguien ENTRÓ al espacio.
        - occupant_name: nombre libre (para visitas)
        - occupant_user_id: id de usuario registrado
        - **kwargs: acepta cualquier dato extra como patente, rut, etc.
        """
        self.occupied_by_name = occupant_name
        self.occupied_by_id = occupant_user_id
        self.occupied_at = datetime.utcnow()
        self.status = 'occupied'
        
        # Si enviaste patente o rut en la ruta, se guardan aquí
        if 'patente' in kwargs:
            self.patente_externa = kwargs.get('patente')
        if 'rut' in kwargs:
            self.rut_externo = kwargs.get('rut')
            
        # Si enviaste datos de vehículo para la visita, los unificamos
        if 'vehicle_make' in kwargs: self.vehicle_make = kwargs.get('vehicle_make')
        if 'vehicle_model' in kwargs: self.vehicle_model = kwargs.get('vehicle_model')
        if 'vehicle_color' in kwargs: self.vehicle_color = kwargs.get('vehicle_color')

        # Determinar nombre para el log
        name = occupant_name
        if occupant_user_id:
            user = db.session.get(User, occupant_user_id)
            if user:
                name = user.full_name
        
        log = ParkingLog(
            parking_spot_id=self.id,
            action='occupied',
            user_id=occupant_user_id,
            performed_by_id=performed_by.id if performed_by else None,
            details=f'Espacio ocupado por {name or "desconocido"}'
        )
        db.session.add(log)

    def vacate(self, performed_by=None):
        """Marcar salida y limpiar datos si era visita"""
        old_name = self.occupant_display_name
        
        # Si NO tiene dueño fijo, limpiamos los datos del vehículo al salir
        if not self.has_owner:
            self.vehicle_plate = None
            self.vehicle_make = None
            self.vehicle_model = None
            self.vehicle_color = None
            self.patente_externa = None
            self.rut_externo = None

        self.occupied_by_id = None
        self.occupied_by_name = None
        self.occupied_at = None
        self.status = 'assigned' if self.has_owner else 'available'
        
        db.session.add(ParkingLog(
            parking_spot_id=self.id, action='vacated',
            performed_by_id=performed_by.id if performed_by else None,
            details=f'Salida de: {old_name or "desconocido"}'
        ))

    @property
    def is_available(self):
        return self.status == 'available' and self.is_active


class ParkingLog(db.Model):
    """Modelo de Historial de Estacionamientos"""
    __tablename__ = 'parking_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    parking_spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', foreign_keys=[user_id])
    
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    
    performed_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    performed_by = db.relationship('User', foreign_keys=[performed_by_id])
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<ParkingLog {self.action} - Spot {self.parking_spot_id}>'