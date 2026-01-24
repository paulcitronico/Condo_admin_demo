import os
from app import create_app, db

# Crear aplicación
app = create_app(os.getenv('FLASK_ENV') or 'development')


@app.shell_context_processor
def make_shell_context():
    """Contexto para flask shell"""
    from app import models
    return {
        'db': db,
        'User': models.User,
        'Role': models.Role,
        'Module': models.Module,
        'ModulePermission': models.ModulePermission,
        'Facility': models.Facility,
        'Booking': models.Booking,
        'ParkingSpot': models.ParkingSpot,
        'ParkingLog': models.ParkingLog,
        'FinancialAccount': models.FinancialAccount,
        'FinancialTransaction': models.FinancialTransaction,
        'ServicePayment': models.ServicePayment,
        'Announcement': models.Announcement,
    }


@app.cli.command()
def init_db():
    """Inicializa la base de datos con datos de ejemplo"""
    # SE CORRIGIÓ: Importación explícita de los modelos necesarios
    from app.models import Facility, ParkingSpot, FinancialAccount, User, Announcement
    from datetime import date, time, timedelta
    
    print("🔄 Creando datos de ejemplo...")
    
    # Crear instalaciones
    facilities_data = [
        {
            'name': 'Quincho',
            'description': 'Área de barbecue con mesas y sillas',
            'capacity': 20,
            'color': '#10B981',
            'icon': '🍖',
            'requires_approval': True
        },
        {
            'name': 'Piscina',
            'description': 'Piscina comunitaria',
            'capacity': 30,
            'color': '#3B82F6',
            'icon': '🏊',
            'requires_approval': False
        },
        {
            'name': 'Gimnasio',
            'description': 'Gimnasio equipado',
            'capacity': 10,
            'color': '#EF4444',
            'icon': '💪',
            'requires_approval': False
        },
        {
            'name': 'Sala de Eventos',
            'description': 'Salón para eventos y reuniones',
            'capacity': 50,
            'color': '#8B5CF6',
            'icon': '🎉',
            'requires_approval': True
        }
    ]
    
    for fac_data in facilities_data:
        if not Facility.query.filter_by(name=fac_data['name']).first():
            facility = Facility(**fac_data)
            db.session.add(facility)
    
    db.session.commit()
    print("✅ Instalaciones creadas")
    
    # Crear espacios de estacionamiento
    floors = ['P1', 'P2']
    sectors = ['A', 'B']
    
    spot_count = 0
    for floor in floors:
        for sector in sectors:
            for i in range(1, 11):  # 10 espacios por sector
                spot_number = f"{floor}-{sector}-{i:02d}"
                
                if not ParkingSpot.query.filter_by(spot_number=spot_number).first():
                    spot_type = 'disabled' if i == 1 else 'regular'
                    spot = ParkingSpot(
                        spot_number=spot_number,
                        floor=floor,
                        sector=sector,
                        spot_type=spot_type,
                        status='available'
                    )
                    db.session.add(spot)
                    spot_count += 1
    
    db.session.commit()
    print(f"✅ {spot_count} espacios de estacionamiento creados")
    
    # Crear cuentas financieras para unidades
    for i in range(1, 21):
        unit_number = f"{i:03d}"
        
        if not FinancialAccount.query.filter_by(unit_number=unit_number).first():
            account = FinancialAccount(
                unit_number=unit_number,
                total_owed=0,
                total_paid=0,
                status='current'
            )
            db.session.add(account)
    
    db.session.commit()
    print("✅ Cuentas financieras creadas")
    
    # Crear un anuncio de ejemplo
    admin = User.query.filter_by(email='admin@condoadmin.com').first()
    if admin and not Announcement.query.first():
        announcement = Announcement(
            title='Bienvenidos al Sistema de Administración',
            content='Este es el nuevo sistema de gestión del condominio. Aquí podrás hacer reservas, ver el estado de tu cuenta y recibir comunicados importantes.',
            priority='information',
            category='notice',
            author_id=admin.id,
            is_published=True
        )
        db.session.add(announcement)
        db.session.commit()
        print("✅ Anuncio de ejemplo creado")
    
    print("\n🎉 ¡Base de datos inicializada con éxito!")
    print("\n👤 Credenciales de acceso:")
    print("   Email: admin@condoadmin.com")
    print("   Password: admin123")
    print("\n⚠️  Recuerda cambiar la contraseña en producción")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)