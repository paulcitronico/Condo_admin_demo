from datetime import datetime
from app import db
from app.models.user import User, Role, Module, ModulePermission
from app.models import Facility, ParkingSpot, FinancialAccount, Announcement

def run_db_initialization():
    """Lógica centralizada para poblar la base de datos"""
    print("🔄 Iniciando inicialización automática de datos...")
    
    # 1. Crear módulos base
    modules_data = [
        {'name': 'roles', 'display_name': 'Gestión de Roles y Permisos'},
        {'name': 'bookings', 'display_name': 'Reserva de Espacios Comunes'},
        {'name': 'parking', 'display_name': 'Estado de Estacionamientos'},
        {'name': 'financials', 'display_name': 'Cuentas y Servicios Pagados'},
        {'name': 'announcements', 'display_name': 'Comunicados Oficiales'},
    ]
    for mod_data in modules_data:
        if not Module.query.filter_by(name=mod_data['name']).first():
            db.session.add(Module(**mod_data))
    db.session.commit()

    # 2. Crear roles y permisos
    roles_config = [
        {
            'name': 'super_admin', 
            'display_name': 'Super Administrador', 
            'permissions': {'roles': 2, 'bookings': 2, 'parking': 2, 'financials': 2, 'announcements': 2}
        },
        {
            'name': 'resident', 
            'display_name': 'Residente', 
            'permissions': {'roles': 0, 'bookings': 2, 'parking': 1, 'financials': 1, 'announcements': 1}
        }
    ]
    for r_data in roles_config:
        if not Role.query.filter_by(name=r_data['name']).first():
            perms = r_data.pop('permissions')
            role = Role(**r_data, description=f"Acceso de {r_data['display_name']}")
            db.session.add(role)
            db.session.flush()
            for module_name, level in perms.items():
                module = Module.query.filter_by(name=module_name).first()
                if module:
                    db.session.add(ModulePermission(role_id=role.id, module_id=module.id, permission_level=level))
    db.session.commit()

    # 3. Instalaciones base
    facilities = [
        {'name': 'Quincho', 'capacity': 20, 'color': '#10B981', 'icon': '🍖', 'requires_approval': True},
        {'name': 'Piscina', 'capacity': 30, 'color': '#3B82F6', 'icon': '🏊', 'requires_approval': False},
        {'name': 'Gimnasio', 'capacity': 10, 'color': '#EF4444', 'icon': '💪', 'requires_approval': False}
    ]
    for fac in facilities:
        if not Facility.query.filter_by(name=fac['name']).first():
            db.session.add(Facility(**fac, description=f"Área de {fac['name']}"))
    
    # 4. Estacionamientos (Ejemplo: 10 espacios)
    if not ParkingSpot.query.first():
        for i in range(1, 11):
            db.session.add(ParkingSpot(
                spot_number=f"P1-A-{i:02d}", floor="P1", sector="A", status="available", spot_type="regular"
            ))

    # 5. Crear usuario administrador
    if not User.query.filter_by(email='admin@condoadmin.com').first():
        admin_role = Role.query.filter_by(name='super_admin').first()
        admin = User(
            email='admin@condoadmin.com', username='admin', 
            first_name='Admin', last_name='Sistema', 
            role_id=admin_role.id, is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)

    db.session.commit()
    print("✅ Base de datos inicializada correctamente.")