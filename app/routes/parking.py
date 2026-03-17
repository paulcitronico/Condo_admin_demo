from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.parking import ParkingSpot, ParkingLog
from app.models.user import User
from app.routes.roles import require_permission

bp = Blueprint('parking', __name__, url_prefix='/parking')


# ═══════════════════════════════════════════════════════
# VISTA PRINCIPAL - MAPA
# ═══════════════════════════════════════════════════════

@bp.route('/')
@login_required
@require_permission('parking', level=1)
def index():
    floor_filter = request.args.get('floor', 'all')
    query = ParkingSpot.query.filter_by(is_active=True)
    
    if floor_filter != 'all':
        query = query.filter_by(floor=floor_filter)
    
    spots = query.order_by(ParkingSpot.row_index, ParkingSpot.col_index).all()
    max_cols = max([s.col_index for s in spots]) + 1 if spots else 1

    # Estadísticas mejoradas
    all_spots = ParkingSpot.query.filter_by(is_active=True).all()
    stats = {
        'total': len(all_spots),
        'green': sum(1 for s in all_spots if s.visual_state == 'green'),
        'blue': sum(1 for s in all_spots if s.visual_state == 'blue'),
        'red': sum(1 for s in all_spots if s.visual_state == 'red'),
        'split': sum(1 for s in all_spots if s.visual_state == 'split'),
    }
    
    floors = db.session.query(ParkingSpot.floor).distinct().all()
    floors = sorted([f[0] for f in floors if f[0]])

    return render_template(
        'parking/index.html',
        spots=spots,
        stats=stats,
        floors=floors,
        current_floor=floor_filter,
        max_cols=max_cols
    )


# ═══════════════════════════════════════════════════════
# CREAR GRILLA
# ═══════════════════════════════════════════════════════

@bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('parking', level=2)
def create():
    if request.method == 'POST':
        floor = request.form.get('floor')
        sector = request.form.get('sector', 'A')
        rows = int(request.form.get('rows', 1))
        cols = int(request.form.get('cols', 1))
        
        try:
            for r in range(rows):
                for c in range(cols):
                    numero_correlativo = (r * cols) + (c + 1)
                    spot_number = f"{floor}-{sector}-{numero_correlativo}"
                    
                    if not ParkingSpot.query.filter_by(spot_number=spot_number).first():
                        new_spot = ParkingSpot(
                            spot_number=spot_number,
                            floor=floor,
                            sector=sector,
                            row_index=r,
                            col_index=c,
                            status='available'
                        )
                        db.session.add(new_spot)
            
            db.session.commit()
            flash('Grilla creada con éxito', 'success')
            return redirect(url_for('parking.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'error')

    return render_template('parking/create.html')


# ═══════════════════════════════════════════════════════
# DETALLE DE ESPACIO
# ═══════════════════════════════════════════════════════

@bp.route('/spot/<int:spot_id>')
@login_required
@require_permission('parking', level=1)
def spot_detail(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    logs = spot.logs.order_by(ParkingLog.created_at.desc()).limit(20).all()
    
    # Usuarios para el formulario de ocupar
    users = User.query.filter_by(is_active=True).order_by(User.last_name).all()
    
    return render_template('parking/detail.html', spot=spot, logs=logs, users=users)


# ═══════════════════════════════════════════════════════
# TOGGLE DISCAPACIDAD
# ═══════════════════════════════════════════════════════

@bp.route('/spot/<int:spot_id>/toggle-disability', methods=['POST'])
@login_required
@require_permission('parking', level=2)
def toggle_disability_status(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)

    if spot.spot_type == 'disability':
        spot.spot_type = 'regular'
        flash(f'Espacio {spot.spot_number} ahora es Regular', 'success')
    else:
        spot.spot_type = 'disability'
        flash(f'Espacio {spot.spot_number} marcado para Discapacidad', 'info')

    db.session.commit()
    return redirect(url_for('parking.spot_detail', spot_id=spot.id))


# ═══════════════════════════════════════════════════════
# ASIGNAR DUEÑO PERMANENTE
# ═══════════════════════════════════════════════════════

@bp.route('/assign/<int:spot_id>', methods=['GET', 'POST'])
@login_required
@require_permission('parking', level=2)
def assign(spot_id):
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
        
        # Horario de disponibilidad
        has_restriction = request.form.get('has_time_restriction') == '1'
        spot.has_time_restriction = has_restriction

        if has_restriction:
            available_from = request.form.get('available_from')
            available_until = request.form.get('available_until')

            if available_from and available_until:
                from datetime import time
                spot.available_from = time.fromisoformat(available_from)
                spot.available_until = time.fromisoformat(available_until)
            else:
                spot.available_from = None
                spot.available_until = None
        else:
            spot.available_from = None
            spot.available_until = None
        
        # Registrar quién hizo la asignación
        log = ParkingLog.query.filter_by(
            parking_spot_id=spot.id,
            action='assigned'
        ).order_by(ParkingLog.created_at.desc()).first()
        
        if log:
            log.performed_by_id = current_user.id
        
        db.session.commit()
        flash(f'Espacio {spot.spot_number} asignado a {user.full_name}', 'success')
        return redirect(url_for('parking.spot_detail', spot_id=spot.id))
    
    users = User.query.filter_by(is_active=True).filter(
        ~User.id.in_(
            db.session.query(ParkingSpot.assigned_user_id).filter(
                ParkingSpot.assigned_user_id.isnot(None)
            )
        )
    ).order_by(User.last_name, User.first_name).all()
    
    return render_template('parking/assign.html', spot=spot, users=users)


# ═══════════════════════════════════════════════════════
# QUITAR DUEÑO PERMANENTE
# ═══════════════════════════════════════════════════════

@bp.route('/unassign/<int:spot_id>', methods=['POST'])
@login_required
@require_permission('parking', level=2)
def unassign(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    if not spot.assigned_user_id:
        flash('Este espacio no está asignado', 'warning')
        return redirect(url_for('parking.spot_detail', spot_id=spot.id))
    
    spot.unassign()
    
    log = ParkingLog.query.filter_by(
        parking_spot_id=spot.id,
        action='unassigned'
    ).order_by(ParkingLog.created_at.desc()).first()
    
    if log:
        log.performed_by_id = current_user.id
    
    db.session.commit()
    flash(f'Espacio {spot.spot_number} liberado exitosamente', 'success')
    return redirect(url_for('parking.spot_detail', spot_id=spot.id))


# ═══════════════════════════════════════════════════════
# OCUPAR ESPACIO (el guardia marca entrada)
# ═══════════════════════════════════════════════════════

@bp.route('/spot/<int:spot_id>/occupy', methods=['POST'])
@login_required
@require_permission('parking', level=2)
def occupy_spot(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)

    # Refrescar desde DB para evitar datos obsoletos
    db.session.refresh(spot)

    # Validaciones base
    if spot.is_physically_occupied:
        flash('El espacio ya está ocupado.', 'warning')
        return redirect(url_for('parking.spot_detail', spot_id=spot.id))

    if spot.under_maintenance:
        flash('El espacio no está disponible porque está fuera de servicio.', 'warning')
        return redirect(url_for('parking.spot_detail', spot_id=spot.id))

    occupy_type = request.form.get('occupy_type', 'visitor')
    patente = request.form.get('patente_externa', '').strip().upper()
    rut = request.form.get('rut_externo', '').strip()

    occupant_user_id = None
    is_owner_entering = False

    # Determinar si quien entra es el dueño asignado
    if occupy_type == 'registered':
        occupant_user_id = request.form.get('occupant_user_id', type=int)

        if not occupant_user_id:
            flash('Selecciona un residente', 'warning')
            return redirect(url_for('parking.spot_detail', spot_id=spot.id))

        if spot.assigned_user_id == occupant_user_id:
            is_owner_entering = True

    # Restricción horaria:
    # solo bloquea a terceros, NO al dueño del estacionamiento
    if (
        spot.has_owner and
        spot.has_time_restriction and
        not spot.is_available_now and
        not is_owner_entering
    ):
        flash('Este espacio no está disponible en este horario.', 'warning')
        return redirect(url_for('parking.spot_detail', spot_id=spot.id))

    # Registrar ocupación
    if occupy_type == 'registered':
        spot.occupy(
            occupant_user_id=occupant_user_id,
            performed_by=current_user,
            patente=patente,
            rut=rut
        )
    else:
        name = request.form.get('occupant_name', '').strip()

        if not name:
            flash('Ingresa el nombre del visitante', 'warning')
            return redirect(url_for('parking.spot_detail', spot_id=spot.id))

        spot.vehicle_plate = patente
        spot.vehicle_make = request.form.get('vehicle_make')
        spot.vehicle_model = request.form.get('vehicle_model')
        spot.vehicle_color = request.form.get('vehicle_color')

        spot.occupy(
            occupant_name=name,
            performed_by=current_user,
            patente=patente,
            rut=rut
        )
    
    db.session.commit()
    flash(f'Espacio {spot.spot_number} ocupado correctamente', 'success')
    return redirect(url_for('parking.spot_detail', spot_id=spot.id))


# ═══════════════════════════════════════════════════════
# DESOCUPAR ESPACIO (el guardia marca salida)
# ═══════════════════════════════════════════════════════

@bp.route('/spot/<int:spot_id>/vacate', methods=['POST'])
@login_required
@require_permission('parking', level=2)
def vacate_spot(spot_id):
    """El guardia marca que el ocupante SE FUE"""
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    if not spot.is_physically_occupied:
        flash('Este espacio no está ocupado', 'warning')
        return redirect(url_for('parking.spot_detail', spot_id=spot.id))
    
    spot.vacate(performed_by=current_user)
    db.session.commit()
    
    flash(f'Espacio {spot.spot_number} desocupado', 'success')
    return redirect(url_for('parking.spot_detail', spot_id=spot.id))


# ═══════════════════════════════════════════════════════
# RESERVAR PARA VISITA
# ═══════════════════════════════════════════════════════

@bp.route('/reserve-visitor/<int:spot_id>', methods=['GET', 'POST'])
@login_required
@require_permission('parking', level=2)
def reserve_visitor(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    if request.method == 'POST':
        visitor_name = request.form.get('visitor_name', '').strip()
        
        spot.status = 'reserved'
        spot.vehicle_plate = request.form.get('vehicle_plate')
        spot.vehicle_model = request.form.get('vehicle_model')
        spot.notes = f"VISITA: {visitor_name}. {request.form.get('notes', '')}"
        
        # También marcamos la ocupación física
        spot.occupied_by_name = visitor_name
        spot.occupied_at = datetime.utcnow()
        
        log = ParkingLog(
            parking_spot_id=spot.id,
            action='reserved',
            performed_by_id=current_user.id,
            details=f'Reservado para visita: {visitor_name}'
        )
        db.session.add(log)
        db.session.commit()
        
        flash(f'Espacio {spot.spot_number} reservado para visita', 'success')
        return redirect(url_for('parking.index'))
    
    return render_template('parking/reserve_visitor.html', spot=spot)


# ═══════════════════════════════════════════════════════
# TOGGLE RÁPIDO (el rayo ⚡ en el mapa)
# ═══════════════════════════════════════════════════════

@bp.route('/toggle-status/<int:spot_id>', methods=['POST'])
@login_required
@require_permission('parking', level=2)
def toggle_status(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    if spot.is_physically_occupied:
        # Si está ocupado -> desocupar
        spot.vacate(performed_by=current_user)
    else:
        # Si está vacío -> marcar como ocupado temporalmente
        spot.occupy(
            occupant_name='Ocupación rápida',
            performed_by=current_user
        )
    
    db.session.commit()
    return redirect(url_for('parking.index'))


# ═══════════════════════════════════════════════════════
# MANTENIMIENTO
# ═══════════════════════════════════════════════════════

@bp.route('/spot/<int:spot_id>/maintenance', methods=['POST'])
@login_required
@require_permission('parking', level=2)
def toggle_maintenance(spot_id):
    spot = ParkingSpot.query.get_or_404(spot_id)
    
    # Cambiar el switch
    spot.under_maintenance = not spot.under_maintenance
    
    # Si se pone en mantenimiento, nos aseguramos de que esté libre
    if spot.under_maintenance and spot.is_physically_occupied:
        spot.vacate(performed_by=current_user)
        
    accion = "FUERA DE SERVICIO" if spot.under_maintenance else "HABILITADO"
    
    log = ParkingLog(
        parking_spot_id=spot.id,
        action='maintenance',
        performed_by_id=current_user.id,
        details=f'Espacio marcado como {accion}'
    )
    db.session.add(log)
    db.session.commit()
    
    flash(f'Espacio {spot.spot_number} ahora está {accion}', 'info')
    return redirect(url_for('parking.spot_detail', spot_id=spot.id))