from datetime import datetime, date, time
from app import db


class Facility(db.Model):
    """Modelo de Instalaciones/Espacios Comunes"""
    __tablename__ = 'facilities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    capacity = db.Column(db.Integer)  # Capacidad de personas
    
    # Configuración
    is_active = db.Column(db.Boolean, default=True)
    requires_approval = db.Column(db.Boolean, default=False)
    max_hours_per_booking = db.Column(db.Integer, default=4)
    min_advance_hours = db.Column(db.Integer, default=24)  # Horas mínimas de anticipación
    
    # Color para el calendario
    color = db.Column(db.String(7), default='#3B82F6')  # Hex color
    icon = db.Column(db.String(50))
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con reservas
    bookings = db.relationship('Booking', backref='facility', lazy='dynamic', 
                              cascade='all, delete-orphan')
    
    def is_available(self, booking_date, start_time, end_time, exclude_booking_id=None):
        """Verifica si la instalación está disponible en el rango de tiempo"""
        query = Booking.query.filter(
            Booking.facility_id == self.id,
            Booking.booking_date == booking_date,
            Booking.status.in_(['pending', 'approved']),
            db.or_(
                db.and_(Booking.start_time <= start_time, Booking.end_time > start_time),
                db.and_(Booking.start_time < end_time, Booking.end_time >= end_time),
                db.and_(Booking.start_time >= start_time, Booking.end_time <= end_time)
            )
        )
        
        if exclude_booking_id:
            query = query.filter(Booking.id != exclude_booking_id)
        
        return query.count() == 0
    
    def __repr__(self):
        return f'<Facility {self.name}>'


class Booking(db.Model):
    """Modelo de Reservas"""
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relaciones
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # SE AGREGA foreign_keys=[user_id]
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('bookings', lazy='dynamic'))
    
    # Fecha y horario
    booking_date = db.Column(db.Date, nullable=False, index=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Detalles
    purpose = db.Column(db.String(255))  # Propósito de la reserva
    num_guests = db.Column(db.Integer)  # Número de invitados
    
    # Estado: pending, approved, rejected, cancelled, completed
    status = db.Column(db.String(20), default='pending', index=True)
    
    # Aprobación/Rechazo
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # Esta ya tenía foreign_keys, la dejamos así:
    approved_by = db.relationship('User', foreign_keys=[approved_by_id])
    approved_at = db.Column(db.DateTime)
    rejection_reason = db.Column(db.Text)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def duration_hours(self):
        """Calcula la duración en horas"""
        if self.start_time and self.end_time:
            start = datetime.combine(date.today(), self.start_time)
            end = datetime.combine(date.today(), self.end_time)
            return (end - start).seconds / 3600
        return 0
    
    def can_cancel(self, user):
        """Verifica si un usuario puede cancelar la reserva"""
        if user.id == self.user_id:
            return self.status in ['pending', 'approved']
        return user.can_write('bookings')
    
    def __repr__(self):
        return f'<Booking {self.facility.name} on {self.booking_date}>'
