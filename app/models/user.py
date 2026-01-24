from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    """Callback para cargar usuario por ID"""
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    """Modelo de Usuario"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    
    # Relación con rol
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    role = db.relationship('Role', backref=db.backref('users', lazy='dynamic'))
    
    # Unidad/departamento (para residentes)
    unit_number = db.Column(db.String(20))
    
    # Estado
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        """Hashear contraseña"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verificar contraseña"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Nombre completo"""
        return f"{self.first_name} {self.last_name}"
    
    def has_permission(self, module_name, required_level=1):
        """
        Verifica si el usuario tiene permiso para un módulo
        required_level: 0=sin acceso, 1=lectura, 2=lectura/escritura
        """
        if not self.is_active:
            return False
        
        permission = ModulePermission.query.join(Module).filter(
            ModulePermission.role_id == self.role_id,
            Module.name == module_name
        ).first()
        
        if not permission:
            return False
        
        return permission.permission_level >= required_level
    
    def can_read(self, module_name):
        """Puede leer el módulo"""
        return self.has_permission(module_name, required_level=1)
    
    def can_write(self, module_name):
        """Puede escribir en el módulo"""
        return self.has_permission(module_name, required_level=2)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Role(db.Model):
    """Modelo de Rol"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    
    is_active = db.Column(db.Boolean, default=True)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con permisos
    permissions = db.relationship('ModulePermission', backref='role', lazy='dynamic', 
                                 cascade='all, delete-orphan')
    
    def get_permission_level(self, module_name):
        """Obtiene el nivel de permiso para un módulo"""
        permission = self.permissions.join(Module).filter(
            Module.name == module_name
        ).first()
        
        return permission.permission_level if permission else 0
    
    def __repr__(self):
        return f'<Role {self.name}>'


class Module(db.Model):
    """Modelo de Módulo del Sistema"""
    __tablename__ = 'modules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    icon = db.Column(db.String(50))  # Ícono CSS/Font Awesome
    
    is_active = db.Column(db.Boolean, default=True)
    order = db.Column(db.Integer, default=0)  # Para ordenar en menú
    
    def __repr__(self):
        return f'<Module {self.name}>'


class ModulePermission(db.Model):
    """Modelo de Permisos por Módulo"""
    __tablename__ = 'module_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('modules.id'), nullable=False)
    
    # Nivel de permiso: 0=sin acceso, 1=lectura, 2=lectura/escritura
    permission_level = db.Column(db.Integer, default=0, nullable=False)
    
    # Auditoría
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con módulo
    module = db.relationship('Module', backref=db.backref('permissions', lazy='dynamic'))
    
    # Constraint único: un rol solo tiene un permiso por módulo
    __table_args__ = (
        db.UniqueConstraint('role_id', 'module_id', name='unique_role_module'),
    )
    
    def __repr__(self):
        return f'<Permission Role:{self.role_id} Module:{self.module_id} Level:{self.permission_level}>'
