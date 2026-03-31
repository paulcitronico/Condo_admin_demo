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
        {'name': 'paqueteria', 'display_name': 'Paquetería y Encomiendas'},
        {'name': 'contacts', 'display_name': 'Contactos Directiva'},
    ]
    for mod_data in modules_data:
        if not Module.query.filter_by(name=mod_data['name']).first():
            db.session.add(Module(**mod_data))
    db.session.commit()

    # 2. Crear roles y permisos - EXPANDIDO CON MÁS ROLES
    roles_config = [
        {
            'name': 'super_admin', 
            'display_name': 'Super Administrador', 
            'is_active': True,
            'permissions': {
                'roles': 2, 'bookings': 2, 'parking': 2, 'financials': 2, 
                'announcements': 2, 'paqueteria': 2, 'contacts': 2
            }
        },
        {
            'name': 'administrator', 
            'display_name': 'Administrador', 
            'is_active': True,
            'permissions': {
                'roles': 1, 'bookings': 2, 'parking': 2, 'financials': 2, 
                'announcements': 2, 'paqueteria': 2, 'contacts': 1
            }
        },
        {
            'name': 'board_member', 
            'display_name': 'Miembro Directiva', 
            'is_active': True,
            'permissions': {
                'roles': 0, 'bookings': 2, 'parking': 1, 'financials': 2, 
                'announcements': 2, 'paqueteria': 1, 'contacts': 2
            }
        },
        {
            'name': 'concierge', 
            'display_name': 'Conserje/Guardia', 
            'is_active': True,
            'permissions': {
                'roles': 0, 'bookings': 1, 'parking': 2, 'financials': 0, 
                'announcements': 1, 'paqueteria': 2, 'contacts': 1
            }
        },
        {
            'name': 'resident', 
            'display_name': 'Residente', 
            'is_active': True,
            'permissions': {
                'roles': 0, 'bookings': 2, 'parking': 1, 'financials': 1, 
                'announcements': 1, 'paqueteria': 0, 'contacts': 1
            }
        },
        {
            'name': 'treasurer', 
            'display_name': 'Tesorero', 
            'is_active': True,
            'permissions': {
                'roles': 0, 'bookings': 1, 'parking': 1, 'financials': 2, 
                'announcements': 1, 'paqueteria': 0, 'contacts': 1
            }
        },
        {
            'name': 'secretary', 
            'display_name': 'Secretario', 
            'is_active': True,
            'permissions': {
                'roles': 0, 'bookings': 2, 'parking': 1, 'financials': 1, 
                'announcements': 2, 'paqueteria': 1, 'contacts': 2
            }
        }
    ]
    
    for r_data in roles_config:
        existing_role = Role.query.filter_by(name=r_data['name']).first()
        if not existing_role:
            perms = r_data.pop('permissions')
            role = Role(
                name=r_data['name'],
                display_name=r_data['display_name'],
                description=f"Acceso de {r_data['display_name']}",
                is_active=r_data['is_active']
            )
            db.session.add(role)
            db.session.flush()
            
            # Asignar permisos a cada módulo
            for module_name, level in perms.items():
                module = Module.query.filter_by(name=module_name).first()
                if module:
                    db.session.add(ModulePermission(
                        role_id=role.id, 
                        module_id=module.id, 
                        permission_level=level
                    ))
            print(f"  ✅ Rol creado: {role.display_name}")
        else:
            # Asegurar que el rol existente esté activo
            if not existing_role.is_active:
                existing_role.is_active = True
                print(f"  🔄 Rol reactivado: {existing_role.display_name}")
    
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
        print(f"  ✅ Usuario admin creado")

    db.session.commit()
    print("✅ Base de datos inicializada correctamente.")
    print(f"📊 Roles disponibles: {Role.query.filter_by(is_active=True).count()}")