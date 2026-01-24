from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.parking import ParkingSpot, ParkingLog
from app.models.user import User
from app.routes.roles import require_permission

bp = Blueprint('parking', __name__, url_prefix='/parking')


# parking.py

@bp.route('/')
@login_required
@require_permission('parking', level=1)
def index():
    # 1. Filtros
    floor_filter = request.args.get('floor', 'all')
    
    # 2. Consulta: Importante usar join con assigned_user para ver quién es el dueño
    query = ParkingSpot.query.filter_by(is_active=True)
    if floor_filter != 'all':
        query = query.filter_by(floor=floor_filter)
    
    spots = query.order_by(ParkingSpot.spot_number).all()
    
    # 3. Estadísticas
    stats = {
        'total': ParkingSpot.query.filter_by(is_active=True).count(),
        'available': ParkingSpot.query.filter_by(status='available', is_active=True).count(),
        'occupied': ParkingSpot.query.filter_by(status='occupied', is_active=True).count(),
        'assigned': ParkingSpot.query.filter(ParkingSpot.assigned_user_id.isnot(None)).count()
    }
    
    # 4. Lista de pisos única
    floors = db.session.query(ParkingSpot.floor).distinct().all()
    floors = sorted([f[0] for f in floors if f[0]])

    return render_template('parking/index.html', 
                         spots=spots, 
                         stats=stats, 
                         floors=floors, 
                         current_floor=floor_filter)
    
@bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('parking', level=2)
def create():
    if request.method == 'POST':
        spot_number = request.form.get('spot_number')
        floor = request.form.get('floor')
        spot_type = request.form.get('spot_type', 'normal')
        
        # Verificar si ya existe
        exists = ParkingSpot.query.filter_by(spot_number=spot_number).first()
        if exists:
            flash('El número de estacionamiento ya existe', 'error')
            return redirect(url_for('parking.create'))

        new_spot = ParkingSpot(
            spot_number=spot_number,
            floor=floor,
            spot_type=spot_type,
            status='available',
            is_active=True
        )
        db.session.add(new_spot)
        db.session.commit()
        flash(f'Espacio {spot_number} creado correctamente', 'success')
        return redirect(url_for('parking.index'))
        
    return render_template('parking/create.html')    

@bp.route('/assign/<int:spot_id>', methods=['GET', 'POST'])
@login_required
@require_permission('parking', level=2)
def assign(spot_id):
    """Asignar espacio de estacionamiento"""
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    if request.method == 'POST':
        user_id = request.form.get('user_id', type=int)
        user = User.query.get_or_404(user_id)
        
        vehicle_data = {
            'plate': request.form.get('vehicle_plate'),
            'make': request.form.get('vehicle_make'),
            'model': request.form.get('vehicle_model'),
            'color': request.form.get('vehicle_color')
        }
        
        spot.assign_to_user(user, vehicle_data)
        spot.notes = request.form.get('notes')
        
        # Registrar quién hizo la asignación
        log = ParkingLog.query.filter_by(
            parking_spot_id=spot.id,
            action='assigned'
        ).order_by(ParkingLog.created_at.desc()).first()
        
        if log:
            log.performed_by_id = current_user.id
        
        db.session.commit()
        
        flash(f'Espacio {spot.spot_number} asignado a {user.full_name}', 'success')
        return redirect(url_for('parking.index'))
    
    # Usuarios sin estacionamiento asignado
    users = User.query.filter_by(is_active=True).filter(
        ~User.id.in_(
            db.session.query(ParkingSpot.assigned_user_id).filter(
                ParkingSpot.assigned_user_id.isnot(None)
            )
        )
    ).order_by(User.last_name, User.first_name).all()
    
    return render_template('parking/assign.html', spot=spot, users=users)


@bp.route('/unassign/<int:spot_id>', methods=['POST'])
@login_required
@require_permission('parking', level=2)
def unassign(spot_id):
    """Liberar espacio de estacionamiento"""
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    if not spot.assigned_user_id:
        flash('Este espacio no está asignado', 'warning')
        return redirect(url_for('parking.index'))
    
    spot.unassign()
    
    # Registrar quién liberó el espacio
    log = ParkingLog.query.filter_by(
        parking_spot_id=spot.id,
        action='unassigned'
    ).order_by(ParkingLog.created_at.desc()).first()
    
    if log:
        log.performed_by_id = current_user.id
    
    db.session.commit()
    
    flash(f'Espacio {spot.spot_number} liberado exitosamente', 'success')
    return redirect(url_for('parking.index'))


@bp.route('/spot/<int:spot_id>')
@login_required
@require_permission('parking', level=1)
def spot_detail(spot_id):
    """Detalle de espacio con historial"""
    spot = ParkingSpot.query.get_or_404(spot_id)
    logs = spot.logs.limit(20).all()
    
    return render_template('parking/detail.html', spot=spot, logs=logs)

@bp.route('/reserve-visitor/<int:spot_id>', methods=['GET', 'POST'])
@login_required
@require_permission('parking', level=2)
def reserve_visitor(spot_id):
    """Reservar un espacio para una visita"""
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    if request.method == 'POST':
        spot.status = 'reserved'
        spot.assigned_user_id = None # No se asigna a un residente
        spot.vehicle_plate = request.form.get('vehicle_plate')
        spot.vehicle_model = request.form.get('vehicle_model')
        # Guardamos el nombre de la visita en las notas
        visitor_name = request.form.get('visitor_name')
        notes = request.form.get('notes')
        spot.notes = f"VISITA: {visitor_name}. {notes}"
        
        db.session.commit()
        flash(f'Espacio {spot.spot_number} reservado para visita', 'success')
        return redirect(url_for('parking.index'))
    
    return render_template('parking/reserve_visitor.html', spot=spot)

@bp.route('/toggle-status/<int:spot_id>', methods=['POST'])
@login_required
@require_permission('parking', level=2)
def toggle_status(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    # Alterna entre disponible y ocupado
    if spot.status == 'available':
        spot.status = 'occupied'
    else:
        spot.status = 'available'
        # Si estaba reservado o asignado, limpiamos las notas de visita si es necesario
        if "VISITA" in (spot.notes or ""):
            spot.notes = None
            
    db.session.commit()
    return redirect(url_for('parking.index'))