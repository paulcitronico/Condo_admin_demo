import sys
import os

# Esto añade la carpeta raíz al camino de búsqueda de Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.parking import ParkingSpot

app = create_app()
with app.app_context():
    # Tu lógica aquí
    for i in range(1, 11):
        spot = ParkingSpot(
            spot_number=f"1-{i:02d}",
            floor="1",
            spot_type="normal",
            status="available",
            is_active=True
        )
        db.session.add(spot)
    
    db.session.commit()
    print("¡Espacios creados!")