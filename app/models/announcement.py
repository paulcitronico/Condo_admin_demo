from datetime import datetime
from app import db


class Announcement(db.Model):
    """Modelo de Comunicados/Anuncios"""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Título y contenido
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    # Prioridad: normal, urgent, information
    priority = db.Column(db.String(20), default='normal', index=True)
    
    # Categoría: maintenance, event, notice, emergency
    category = db.Column(db.String(50), index=True)
    
    # Publicación
    is_published = db.Column(db.Boolean, default=True, index=True)
    publish_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)  # Fecha de expiración (opcional)
    
    # Autor
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    author = db.relationship('User', backref=db.backref('announcements', lazy='dynamic'))
    
    # Área afectada (opcional)
    affected_area = db.Column(db.String(100))  # Ej: "Torre B", "Piscina", "Todo el edificio"
    
    # Adjuntos (URLs separadas por comas)
    attachments = db.Column(db.Text)
    
    # Visto por
    views_count = db.Column(db.Integer, default=0)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con confirmaciones de lectura
    acknowledgments = db.relationship('AnnouncementAcknowledgment', backref='announcement',
                                     lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def is_active(self):
        """Verifica si el anuncio está activo"""
        if not self.is_published:
            return False
        if self.expiry_date and datetime.utcnow() > self.expiry_date:
            return False
        return True
    
    def acknowledge_by(self, user):
        """Marca como leído por un usuario"""
        ack = AnnouncementAcknowledgment.query.filter_by(
            announcement_id=self.id,
            user_id=user.id
        ).first()
        
        if not ack:
            ack = AnnouncementAcknowledgment(
                announcement_id=self.id,
                user_id=user.id
            )
            db.session.add(ack)
            self.views_count += 1
    
    def is_acknowledged_by(self, user):
        """Verifica si fue leído por un usuario"""
        return AnnouncementAcknowledgment.query.filter_by(
            announcement_id=self.id,
            user_id=user.id
        ).first() is not None
    
    def get_acknowledgment_stats(self):
        """Estadísticas de confirmación de lectura"""
        from app.models.user import User
        
        total_users = User.query.filter_by(is_active=True).count()
        acknowledged = self.acknowledgments.count()
        
        return {
            'total': total_users,
            'acknowledged': acknowledged,
            'pending': total_users - acknowledged,
            'percentage': (acknowledged / total_users * 100) if total_users > 0 else 0
        }
    
    def __repr__(self):
        return f'<Announcement {self.title}>'


class AnnouncementAcknowledgment(db.Model):
    """Modelo de Confirmación de Lectura de Anuncios"""
    __tablename__ = 'announcement_acknowledgments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User')
    
    # Timestamp de lectura
    acknowledged_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Constraint único: un usuario solo puede confirmar una vez
    __table_args__ = (
        db.UniqueConstraint('announcement_id', 'user_id', name='unique_announcement_user'),
    )
    
    def __repr__(self):
        return f'<Acknowledgment Announcement:{self.announcement_id} User:{self.user_id}>'


class AnnouncementComment(db.Model):
    """Modelo de Comentarios en Anuncios (opcional)"""
    __tablename__ = 'announcement_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    announcement_id = db.Column(db.Integer, db.ForeignKey('announcements.id'), nullable=False)
    announcement = db.relationship('Announcement', backref=db.backref('comments', lazy='dynamic',
                                                                      cascade='all, delete-orphan'))
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User')
    
    content = db.Column(db.Text, nullable=False)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Comment on Announcement:{self.announcement_id}>'
