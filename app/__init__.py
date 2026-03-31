from flask import Flask, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import config
from datetime import datetime
import pytz

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Filtros y procesadores
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    @app.template_filter('localtime')
    def localtime_filter(utc_dt):
        if not utc_dt: return ''
        tz = pytz.timezone(app.config.get('TIMEZONE', 'America/Santiago'))
        if utc_dt.tzinfo is None: utc_dt = pytz.utc.localize(utc_dt)
        return utc_dt.astimezone(tz).strftime('%d/%m/%Y %H:%M')

    # NUEVO FILTRO: month_name para convertir número de mes a nombre
    @app.template_filter('month_name')
    def month_name_filter(month_number):
        """Convierte un número de mes (1-12) a su nombre en español"""
        months = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return months.get(month_number, 'Desconocido')

    # Registro de Blueprints
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

    # Redirección de raíz
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Inicialización automática inteligente
    with app.app_context():
        db.create_all()
        from app.models.user import User
        # Solo ejecuta si el administrador no existe (primera vez)
        if not User.query.filter_by(email='admin@condoadmin.com').first():
            from app.utils import run_db_initialization
            run_db_initialization()
    
    return app