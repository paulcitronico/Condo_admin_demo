import os
from app import create_app

# Crear aplicación según entorno
app = create_app(os.getenv('FLASK_ENV') or 'development')

@app.cli.command()
def init_db():
    """Comando manual para forzar la creación de datos"""
    from app.utils import run_db_initialization
    run_db_initialization()

if __name__ == '__main__':
    # Railway requiere el host 0.0.0.0 y el puerto de la variable de entorno PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)