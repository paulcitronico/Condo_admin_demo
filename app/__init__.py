from flask import Flask, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
from datetime import datetime
import pytz  # Para manejo de zona horaria

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name='default'):
    """Factory para crear la aplicación Flask"""
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    # ========== FILTROS Y CONTEXT PROCESSORS ==========
    @app.template_filter('month_name')
    def month_name_filter(month_number):
        months = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        return months[month_number] if 1 <= month_number <= 12 else ''

    @app.template_filter('linebreaks')
    def linebreaks_filter(text):
        if not text:
            return ''
        return text.replace('\n', '<br>')

    @app.template_filter('localtime')
    def localtime_filter(utc_dt):
        if utc_dt is None:
            return ''
        tz = pytz.timezone(app.config.get('TIMEZONE', 'UTC'))
        if utc_dt.tzinfo is None:
            utc_dt = pytz.utc.localize(utc_dt)
        local_dt = utc_dt.astimezone(tz)
        return local_dt.strftime('%d/%m/%Y %H:%M')

    @app.context_processor
    def inject_now():
        # Único punto de verdad para la variable 'now' en templates
        return {'now': datetime.utcnow()}
    
    # Registrar blueprints
    from app.routes import auth, dashboard, roles, bookings, parking, financials, announcements, contacts, rules
    from app.routes.paqueteria import bp as paqueteria_bp
    from app.routes.comprobante import bp as comprobante_bp
    
    app.register_blueprint(paqueteria_bp)
    app.register_blueprint(comprobante_bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(roles.bp)
    app.register_blueprint(bookings.bp)
    app.register_blueprint(parking.bp)
    app.register_blueprint(financials.bp)
    app.register_blueprint(announcements.bp)
    app.register_blueprint(contacts.bp)
    app.register_blueprint(rules.bp)

    # SOLUCIÓN ERROR 500: Ruta raíz redirige al login
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # SOLUCIÓN RATE LIMIT: Se desactiva la inicialización automática en el arranque.
    # Para inicializar la DB, usa el comando: flask init-db
    """
    with app.app_context():
        db.create_all()
        init_default_data()
    """
    
    return app


def init_default_data():
    """Inicializa roles y usuario admin por defecto"""
    from app.models.user import Role, User, Module, ModulePermission
    
    # Crear módulos si no existen
    modules_data = [
        {'name': 'roles', 'display_name': 'Gestión de Roles y Permisos'},
        {'name': 'bookings', 'display_name': 'Reserva de Espacios Comunes'},
        {'name': 'parking', 'display_name': 'Estado de Estacionamientos'},
        {'name': 'financials', 'display_name': 'Cuentas y Servicios Pagados'},
        {'name': 'announcements', 'display_name': 'Comunicados Oficiales'},
    ]
    
    for mod_data in modules_data:
        if not Module.query.filter_by(name=mod_data['name']).first():
            module = Module(**mod_data)
            db.session.add(module)
    
    db.session.commit()
    
    # Crear roles por defecto
    roles_data = [
        {
            'name': 'super_admin',
            'display_name': 'Super Administrador',
            'description': 'Acceso completo a todos los módulos',
            'permissions': {'roles': 2, 'bookings': 2, 'parking': 2, 'financials': 2, 'announcements': 2}
        },
        {
            'name': 'administrator',
            'display_name': 'Administrador',
            'description': 'Gestión operativa del condominio',
            'permissions': {'roles': 1, 'bookings': 2, 'parking': 2, 'financials': 2, 'announcements': 2}
        },
        {
            'name': 'security_guard',
            'display_name': 'Guardia de Seguridad',
            'description': 'Control de accesos y estacionamientos',
            'permissions': {'roles': 0, 'bookings': 1, 'parking': 2, 'financials': 0, 'announcements': 1}
        },
        {
            'name': 'board_member',
            'display_name': 'Miembro de Directiva',
            'description': 'Supervisión y aprobaciones',
            'permissions': {'roles': 1, 'bookings': 2, 'parking': 1, 'financials': 2, 'announcements': 2}
        },
        {
            'name': 'resident',
            'display_name': 'Residente',
            'description': 'Acceso básico para residentes',
            'permissions': {'roles': 0, 'bookings': 2, 'parking': 1, 'financials': 1, 'announcements': 1}
        }
    ]
    
    for role_data in roles_data:
        if not Role.query.filter_by(name=role_data['name']).first():
            permissions = role_data.pop('permissions')
            role = Role(**role_data)
            db.session.add(role)
            db.session.flush()
            
            for module_name, level in permissions.items():
                module = Module.query.filter_by(name=module_name).first()
                if module:
                    perm = ModulePermission(
                        role_id=role.id,
                        module_id=module.id,
                        permission_level=level
                    )
                    db.session.add(perm)
    
    db.session.commit()
    
    # Crear usuario admin
    if not User.query.filter_by(email='admin@condoadmin.com').first():
        admin_role = Role.query.filter_by(name='super_admin').first()
        admin_user = User(
            email='admin@condoadmin.com',
            username='admin',
            first_name='Administrador',
            last_name='Sistema',
            role_id=admin_role.id,
            is_active=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
