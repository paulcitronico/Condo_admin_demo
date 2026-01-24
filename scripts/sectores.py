# create_facilities.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.booking import Facility

app = create_app()

with app.app_context():
    # Verificar si ya hay instalaciones
    if Facility.query.count() == 0:
        # Crear instalaciones comunes de un condominio
        facilities = [
            {
                'name': 'Sala de Reuniones',
                'description': 'Sala para reuniones y eventos sociales',
                'capacity': 30,
                'requires_approval': False,
                'max_hours_per_booking': 4,
                'min_advance_hours': 24,
                'color': '#3B82F6',
                'icon': 'fa-users'
            },
            {
                'name': 'Gimnasio',
                'description': 'Área de ejercicio con equipamiento básico',
                'capacity': 10,
                'requires_approval': False,
                'max_hours_per_booking': 2,
                'min_advance_hours': 1,
                'color': '#10B981',
                'icon': 'fa-dumbbell'
            },
            {
                'name': 'Piscina',
                'description': 'Piscina comunitaria',
                'capacity': 20,
                'requires_approval': True,
                'max_hours_per_booking': 3,
                'min_advance_hours': 48,
                'color': '#06B6D4',
                'icon': 'fa-swimming-pool'
            },
            {
                'name': 'Salón de Eventos',
                'description': 'Espacio para fiestas y celebraciones grandes',
                'capacity': 100,
                'requires_approval': True,
                'max_hours_per_booking': 6,
                'min_advance_hours': 72,
                'color': '#8B5CF6',
                'icon': 'fa-glass-cheers'
            },
            {
                'name': 'Cancha de Tenis',
                'description': 'Cancha de tenis con iluminación nocturna',
                'capacity': 4,
                'requires_approval': False,
                'max_hours_per_booking': 2,
                'min_advance_hours': 24,
                'color': '#F59E0B',
                'icon': 'fa-baseball-ball'
            },
            {
                'name': 'Área de BBQ',
                'description': 'Zona con parrillas y mesas para asados',
                'capacity': 15,
                'requires_approval': False,
                'max_hours_per_booking': 4,
                'min_advance_hours': 48,
                'color': '#EF4444',
                'icon': 'fa-fire'
            }
        ]
        
        for facility_data in facilities:
            facility = Facility(**facility_data)
            db.session.add(facility)
        
        db.session.commit()
        print(f"✅ Creadas {len(facilities)} instalaciones exitosamente!")
    else:
        print("⚠️ Ya existen instalaciones en la base de datos:")
        for facility in Facility.query.all():
            print(f"  - {facility.name} (ID: {facility.id})")