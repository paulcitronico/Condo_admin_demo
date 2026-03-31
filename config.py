import os
from datetime import timedelta

# Obtener el directorio base del proyecto (donde está este archivo)
basedir = os.path.abspath(os.path.dirname(__file__))

# Asegurar que el directorio de instancia exista
instance_dir = os.path.join(basedir, 'instance')
os.makedirs(instance_dir, exist_ok=True)


class Config:
    """Configuración base para la aplicación"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'clave-super-secreta-cambiala-en-produccion'
    
    # FIX: Ruta absoluta y explícita para SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(instance_dir, 'condo_admin.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuración de uploads (para futuras imágenes/documentos)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    
    # Asegurar que existe el directorio de uploads
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # Zona horaria
    TIMEZONE = 'America/Santiago'


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Muestra queries SQL en consola


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True


class TestingConfig(Config):
    """Configuración para tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}