# seed_modules.py - Script para poblar módulos iniciales
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# scripts/seed_data.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import Module, Role, ModulePermission

def seed_modules_and_roles():
    """Poblar la base de datos con módulos y roles iniciales"""
    app = create_app()
    
    with app.app_context():
        try:
            print("Inicializando módulos y roles del sistema...")
            
            # Definir módulos del sistema ERP
            modules_data = [
                # Módulos principales
                {'name': 'dashboard', 'display_name': 'Panel Principal', 'icon': 'tachometer-alt', 'order': 1, 'route': 'dashboard.index'},
                {'name': 'bookings', 'display_name': 'Reservas de Áreas', 'icon': 'calendar-check', 'order': 2, 'route': 'bookings.index'},
                {'name': 'parking', 'display_name': 'Estacionamiento', 'icon': 'parking', 'order': 3, 'route': 'parking.index'},
                {'name': 'financials', 'display_name': 'Finanzas', 'icon': 'chart-line', 'order': 4, 'route': 'financials.index'},
                {'name': 'announcements', 'display_name': 'Anuncios', 'icon': 'bullhorn', 'order': 5, 'route': 'announcements.index'},
                {'name': 'roles', 'display_name': 'Roles y Permisos', 'icon': 'user-shield', 'order': 6, 'route': 'roles.index'},
            ]
            
            for mod_data in modules_data:
                module = Module.query.filter_by(name=mod_data['name']).first()
                if not module:
                    module = Module(**mod_data)
                    db.session.add(module)
                    print(f"✓ Módulo creado: {mod_data['display_name']}")
            
            db.session.commit()
            
            # Crear roles del sistema
            roles_data = [
                {'name': 'super_admin', 'display_name': 'Super Administrador', 'is_system': True, 'description': 'Acceso total al sistema'},
                {'name': 'administrator', 'display_name': 'Administrador', 'is_system': False, 'description': 'Administrador del condominio'},
                {'name': 'board_member', 'display_name': 'Miembro de Junta', 'is_system': False, 'description': 'Miembro de la junta directiva'},
                {'name': 'security_guard', 'display_name': 'Guardia de Seguridad', 'is_system': False, 'description': 'Personal de seguridad'},
                {'name': 'resident', 'display_name': 'Residente', 'is_system': False, 'description': 'Residente del condominio'},
                {'name': 'vendor', 'display_name': 'Proveedor', 'is_system': False, 'description': 'Proveedor externo'},
            ]
            
            for role_data in roles_data:
                role = Role.query.filter_by(name=role_data['name']).first()
                if not role:
                    role = Role(**role_data)
                    db.session.add(role)
                    print(f"✓ Rol creado: {role_data['display_name']}")
            
            db.session.commit()
            
            # Asignar permisos completos al super_admin
            super_admin = Role.query.filter_by(name='super_admin').first()
            modules = Module.query.all()
            
            for module in modules:
                perm = ModulePermission.query.filter_by(
                    role_id=super_admin.id,
                    module_id=module.id
                ).first()
                
                if not perm:
                    perm = ModulePermission(
                        role_id=super_admin.id,
                        module_id=module.id,
                        permission_level=3  # Nivel admin
                    )
                    db.session.add(perm)
            
            db.session.commit()
            
            # Asignar permisos básicos al residente
            resident = Role.query.filter_by(name='resident').first()
            resident_modules = ['dashboard', 'bookings', 'parking', 'announcements']
            
            for mod_name in resident_modules:
                module = Module.query.filter_by(name=mod_name).first()
                if module:
                    perm = ModulePermission.query.filter_by(
                        role_id=resident.id,
                        module_id=module.id
                    ).first()
                    
                    if not perm:
                        perm = ModulePermission(
                            role_id=resident.id,
                            module_id=module.id,
                            permission_level=1  # Solo lectura
                        )
                        db.session.add(perm)
            
            db.session.commit()
            
            print("\n✅ Inicialización completada exitosamente!")
            print("\nRoles creados:")
            roles = Role.query.all()
            for role in roles:
                print(f"  - {role.display_name} ({role.name})")
            
            print("\nMódulos creados:")
            for module in Module.query.all():
                print(f"  - {module.display_name} ({module.name})")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error durante la inicialización: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    seed_modules_and_roles()