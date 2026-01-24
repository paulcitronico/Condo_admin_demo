from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models.user import User, Role, Module, ModulePermission

bp = Blueprint('roles', __name__, url_prefix='/roles')


def require_permission(module_name, level=1):
    """Decorador para verificar permisos"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.has_permission(module_name, level):
                flash('No tienes permisos para acceder a esta sección', 'error')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@bp.route('/')
@login_required
@require_permission('roles', level=1)
def index():
    """Lista de roles y permisos"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    roles = Role.query.filter_by(is_active=True).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    modules = Module.query.filter_by(is_active=True).order_by(Module.order).all()
    
    return render_template('roles/index.html', roles=roles, modules=modules)


@bp.route('/users')
@login_required
@require_permission('roles', level=1)
def users():
    """Lista de usuarios y sus roles"""
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', None)
    status_filter = request.args.get('status', 'all')
    
    query = User.query
    
    if role_filter:
        query = query.filter_by(role_id=role_filter)
    
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'inactive':
        query = query.filter_by(is_active=False)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    roles = Role.query.filter_by(is_active=True).all()
    
    return render_template('roles/users.html', users=users, roles=roles)


@bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('roles', level=2)
def edit_user(user_id):
    """Editar usuario y rol"""
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.email = request.form.get('email')
        user.phone = request.form.get('phone')
        user.unit_number = request.form.get('unit_number')
        user.role_id = request.form.get('role_id', type=int)
        user.is_active = request.form.get('is_active') == 'on'
        
        # Cambiar contraseña si se proporciona
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash(f'Usuario {user.full_name} actualizado exitosamente', 'success')
        return redirect(url_for('roles.users'))
    
    roles = Role.query.filter_by(is_active=True).all()
    return render_template('roles/edit_user.html', user=user, roles=roles)


@bp.route('/role/<int:role_id>/permissions', methods=['GET', 'POST'])
@login_required
@require_permission('roles', level=2)
def edit_role_permissions(role_id):
    """Editar permisos de un rol"""
    role = Role.query.get_or_404(role_id)
    modules = Module.query.filter_by(is_active=True).order_by(Module.order).all()
    
    if request.method == 'POST':
        for module in modules:
            permission_level = request.form.get(f'permission_{module.id}', 0, type=int)
            
            # Buscar o crear permiso
            perm = ModulePermission.query.filter_by(
                role_id=role.id,
                module_id=module.id
            ).first()
            
            if perm:
                perm.permission_level = permission_level
            else:
                perm = ModulePermission(
                    role_id=role.id,
                    module_id=module.id,
                    permission_level=permission_level
                )
                db.session.add(perm)
        
        db.session.commit()
        flash(f'Permisos del rol {role.display_name} actualizados', 'success')
        return redirect(url_for('roles.index'))
    
    # Obtener permisos actuales
    current_permissions = {}
    for module in modules:
        perm = ModulePermission.query.filter_by(
            role_id=role.id,
            module_id=module.id
        ).first()
        current_permissions[module.id] = perm.permission_level if perm else 0
    
    return render_template('roles/edit_permissions.html', 
                         role=role, 
                         modules=modules,
                         current_permissions=current_permissions)


@bp.route('/user/create', methods=['GET', 'POST'])
@login_required
@require_permission('roles', level=2)
def create_user():
    """Crear nuevo usuario"""
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        
        # Validar duplicados
        if User.query.filter_by(email=email).first():
            flash('El email ya está registrado', 'error')
            return redirect(url_for('roles.create_user'))
        
        if User.query.filter_by(username=username).first():
            flash('El nombre de usuario ya existe', 'error')
            return redirect(url_for('roles.create_user'))
        
        user = User(
            email=email,
            username=username,
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            phone=request.form.get('phone'),
            unit_number=request.form.get('unit_number'),
            role_id=request.form.get('role_id', type=int),
            is_active=True
        )
        user.set_password(request.form.get('password'))
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuario {user.full_name} creado exitosamente', 'success')
        return redirect(url_for('roles.users'))
    
    roles = Role.query.filter_by(is_active=True).all()
    return render_template('roles/create_user.html', roles=roles)