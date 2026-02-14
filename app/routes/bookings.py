from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app import db
from app.models.booking import Facility, Booking
from app.models import User
from app.routes.roles import require_permission

bp = Blueprint('bookings', __name__, url_prefix='/bookings')


@bp.route('/')
@login_required
@require_permission('bookings', level=1)
def index():
    """Vista de calendario de reservas"""
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    
    start_date = date(year, month, 1)
    end_date = date(year + (1 if month == 12 else 0), (month % 12) + 1 if month != 12 else 1, 1)
    
    # Obtener reservas con JOIN para evitar problemas de lazy loading
    query = db.session.query(Booking, Facility, User).join(
        Facility, Booking.facility_id == Facility.id
    ).join(
        User, Booking.user_id == User.id
    ).filter(
        Booking.booking_date >= start_date,
        Booking.booking_date < end_date,
        Booking.status != 'cancelled'
    ).order_by(Booking.booking_date, Booking.start_time)
    
    bookings = query.all()
    
    # Formatear eventos para FullCalendar
    events = []
    for booking, facility, user in bookings:
        events.append({
            'id': booking.id,
            'title': f"{facility.name} - {user.full_name}",
            'start': f"{booking.booking_date.isoformat()}T{booking.start_time.isoformat()}",
            'end': f"{booking.booking_date.isoformat()}T{booking.end_time.isoformat()}",
            'color': facility.color,
            'status': booking.status,
            'is_mine': booking.user_id == current_user.id,
            'allDay': False
        })
    
    facilities = Facility.query.filter_by(is_active=True).all()
    
    return render_template('bookings/index.html',
                         facilities=facilities,
                         events=events,
                         year=year,
                         month=month)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('bookings', level=2)
def create():
    """Crear nueva reserva"""
    # CÓDIGO DEBUG TEMPORAL - INICIO
    facilities = Facility.query.filter_by(is_active=True).all()
    print(f"=== DEBUG: {len(facilities)} instalaciones encontradas ===")  # Ver en consola
    if not facilities:
        flash('No hay instalaciones disponibles. Contacta al administrador.', 'warning')
    # CÓDIGO DEBUG TEMPORAL - FIN

    """Crear nueva reserva"""
    if request.method == 'POST':
        facility_id = request.form.get('facility_id', type=int)
        booking_date = datetime.strptime(request.form.get('booking_date'), '%Y-%m-%d').date()
        start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        
        facility = Facility.query.get_or_404(facility_id)
        
        # Verificar disponibilidad
        if not facility.is_available(booking_date, start_time, end_time):
            flash('La instalación no está disponible en ese horario', 'error')
            return redirect(url_for('bookings.create'))
        
        # Crear reserva
        booking = Booking(
            facility_id=facility_id,
            user_id=current_user.id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            purpose=request.form.get('purpose'),
            num_guests=request.form.get('num_guests', type=int),
            status='approved' if not facility.requires_approval else 'pending'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        status_msg = 'pendiente de aprobación' if facility.requires_approval else 'confirmada'
        flash(f'Reserva creada exitosamente ({status_msg})', 'success')
        return redirect(url_for('bookings.index'))
    
    facilities = Facility.query.filter_by(is_active=True).all()
    return render_template('bookings/create.html', facilities=facilities)


@bp.route('/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel(booking_id):
    """Cancelar reserva"""
    booking = Booking.query.get_or_404(booking_id)
    
    if not booking.can_cancel(current_user):
        flash('No puedes cancelar esta reserva', 'error')
        return redirect(url_for('bookings.index'))
    
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('Reserva cancelada exitosamente', 'success')
    return redirect(url_for('bookings.index'))


@bp.route('/api/availability', methods=['POST'])
@login_required
def check_availability():
    """API para verificar disponibilidad"""
    data = request.get_json()
    
    facility_id = data.get('facility_id')
    booking_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
    start_time = datetime.strptime(data['start_time'], '%H:%M').time()
    end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    
    facility = Facility.query.get_or_404(facility_id)
    available = facility.is_available(booking_date, start_time, end_time)
    
    return jsonify({'available': available})

# Añade esto a bookings.py (preferiblemente antes de las APIs)

@bp.route('/<int:booking_id>/detail')
@login_required
def detail(booking_id):
    """Vista de detalle de una reserva específica"""
    # Buscamos la reserva o lanzamos 404 si no existe
    booking = Booking.query.get_or_404(booking_id)
    
    return render_template('bookings/detail.html', booking=booking)

# ═══════════════════════════════════════════════════════
# CRUD DE INSTALACIONES
# ═══════════════════════════════════════════════════════

@bp.route('/facilities')
@login_required
@require_permission('bookings', level=1)
def facilities_list():
    """Lista todas las instalaciones"""
    facilities = Facility.query.order_by(Facility.name).all()
    
    # Estadísticas por instalación
    for facility in facilities:
        facility.total_bookings = Booking.query.filter_by(
            facility_id=facility.id
        ).filter(Booking.status != 'cancelled').count()
        
        facility.pending_bookings = Booking.query.filter_by(
            facility_id=facility.id, 
            status='pending'
        ).count()
        
        # Próxima reserva
        from datetime import date as date_today
        facility.next_booking = Booking.query.filter(
            Booking.facility_id == facility.id,
            Booking.booking_date >= date_today.today(),
            Booking.status.in_(['pending', 'approved'])
        ).order_by(Booking.booking_date, Booking.start_time).first()
    
    return render_template('bookings/facilities_list.html', facilities=facilities)


@bp.route('/facilities/create', methods=['GET', 'POST'])
@login_required
@require_permission('bookings', level=2)
def facility_create():
    """Crear nueva instalación"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('El nombre de la instalación es obligatorio', 'error')
            return redirect(url_for('bookings.facility_create'))
        
        # Verificar que no exista otra con el mismo nombre
        existing = Facility.query.filter(
            db.func.lower(Facility.name) == name.lower()
        ).first()
        
        if existing:
            flash(f'Ya existe una instalación llamada "{name}"', 'error')
            return redirect(url_for('bookings.facility_create'))
        
        facility = Facility(
            name=name,
            description=request.form.get('description', '').strip(),
            capacity=request.form.get('capacity', 0, type=int),
            is_active=request.form.get('is_active') == 'on',
            requires_approval=request.form.get('requires_approval') == 'on',
            max_hours_per_booking=request.form.get('max_hours_per_booking', 4, type=int),
            min_advance_hours=request.form.get('min_advance_hours', 24, type=int),
            color=request.form.get('color', '#3B82F6'),
            icon=request.form.get('icon', 'fa-building')
        )
        
        db.session.add(facility)
        db.session.commit()
        
        flash(f'Instalación "{name}" creada exitosamente', 'success')
        return redirect(url_for('bookings.facilities_list'))
    
    # Lista de íconos disponibles para elegir
    icons = [
        {'value': 'fa-swimming-pool', 'label': 'Piscina', 'emoji': '🏊'},
        {'value': 'fa-dumbbell', 'label': 'Gimnasio', 'emoji': '🏋️'},
        {'value': 'fa-fire', 'label': 'Quincho/BBQ', 'emoji': '🔥'},
        {'value': 'fa-futbol', 'label': 'Cancha', 'emoji': '⚽'},
        {'value': 'fa-table-tennis', 'label': 'Ping Pong', 'emoji': '🏓'},
        {'value': 'fa-users', 'label': 'Salón de Eventos', 'emoji': '🎉'},
        {'value': 'fa-couch', 'label': 'Sala de Estar', 'emoji': '🛋️'},
        {'value': 'fa-baby', 'label': 'Juegos Infantiles', 'emoji': '👶'},
        {'value': 'fa-hot-tub', 'label': 'Jacuzzi/Spa', 'emoji': '🛁'},
        {'value': 'fa-tv', 'label': 'Sala de Cine', 'emoji': '🎬'},
        {'value': 'fa-dog', 'label': 'Área de Mascotas', 'emoji': '🐕'},
        {'value': 'fa-tree', 'label': 'Jardín/Terraza', 'emoji': '🌳'},
        {'value': 'fa-building', 'label': 'Otro', 'emoji': '🏢'},
    ]
    
    return render_template('bookings/facility_form.html', 
                         facility=None, icons=icons, 
                         form_action=url_for('bookings.facility_create'))


@bp.route('/facilities/<int:facility_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('bookings', level=2)
def facility_edit(facility_id):
    """Editar instalación existente"""
    facility = Facility.query.get_or_404(facility_id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        
        if not name:
            flash('El nombre es obligatorio', 'error')
            return redirect(url_for('bookings.facility_edit', facility_id=facility_id))
        
        # Verificar nombre duplicado (excluyendo la actual)
        existing = Facility.query.filter(
            db.func.lower(Facility.name) == name.lower(),
            Facility.id != facility_id
        ).first()
        
        if existing:
            flash(f'Ya existe otra instalación llamada "{name}"', 'error')
            return redirect(url_for('bookings.facility_edit', facility_id=facility_id))
        
        facility.name = name
        facility.description = request.form.get('description', '').strip()
        facility.capacity = request.form.get('capacity', 0, type=int)
        facility.is_active = request.form.get('is_active') == 'on'
        facility.requires_approval = request.form.get('requires_approval') == 'on'
        facility.max_hours_per_booking = request.form.get('max_hours_per_booking', 4, type=int)
        facility.min_advance_hours = request.form.get('min_advance_hours', 24, type=int)
        facility.color = request.form.get('color', '#3B82F6')
        facility.icon = request.form.get('icon', 'fa-building')
        
        db.session.commit()
        
        flash(f'Instalación "{name}" actualizada exitosamente', 'success')
        return redirect(url_for('bookings.facilities_list'))
    
    icons = [
        {'value': 'fa-swimming-pool', 'label': 'Piscina', 'emoji': '🏊'},
        {'value': 'fa-dumbbell', 'label': 'Gimnasio', 'emoji': '🏋️'},
        {'value': 'fa-fire', 'label': 'Quincho/BBQ', 'emoji': '🔥'},
        {'value': 'fa-futbol', 'label': 'Cancha', 'emoji': '⚽'},
        {'value': 'fa-table-tennis', 'label': 'Ping Pong', 'emoji': '🏓'},
        {'value': 'fa-users', 'label': 'Salón de Eventos', 'emoji': '🎉'},
        {'value': 'fa-couch', 'label': 'Sala de Estar', 'emoji': '🛋️'},
        {'value': 'fa-baby', 'label': 'Juegos Infantiles', 'emoji': '👶'},
        {'value': 'fa-hot-tub', 'label': 'Jacuzzi/Spa', 'emoji': '🛁'},
        {'value': 'fa-tv', 'label': 'Sala de Cine', 'emoji': '🎬'},
        {'value': 'fa-dog', 'label': 'Área de Mascotas', 'emoji': '🐕'},
        {'value': 'fa-tree', 'label': 'Jardín/Terraza', 'emoji': '🌳'},
        {'value': 'fa-building', 'label': 'Otro', 'emoji': '🏢'},
    ]
    
    return render_template('bookings/facility_form.html', 
                         facility=facility, icons=icons,
                         form_action=url_for('bookings.facility_edit', facility_id=facility_id))


@bp.route('/facilities/<int:facility_id>/toggle', methods=['POST'])
@login_required
@require_permission('bookings', level=2)
def facility_toggle(facility_id):
    """Activar/Desactivar instalación"""
    facility = Facility.query.get_or_404(facility_id)
    facility.is_active = not facility.is_active
    db.session.commit()
    
    estado = 'activada' if facility.is_active else 'desactivada'
    flash(f'Instalación "{facility.name}" {estado}', 'success')
    return redirect(url_for('bookings.facilities_list'))


@bp.route('/facilities/<int:facility_id>/delete', methods=['POST'])
@login_required
@require_permission('bookings', level=2)
def facility_delete(facility_id):
    """Eliminar instalación"""
    facility = Facility.query.get_or_404(facility_id)
    
    # Verificar si tiene reservas activas
    active_bookings = Booking.query.filter(
        Booking.facility_id == facility_id,
        Booking.status.in_(['pending', 'approved']),
        Booking.booking_date >= date.today()
    ).count()
    
    if active_bookings > 0:
        flash(f'No se puede eliminar "{facility.name}" porque tiene {active_bookings} reserva(s) activa(s). Desactívala primero.', 'error')
        return redirect(url_for('bookings.facilities_list'))
    
    name = facility.name
    db.session.delete(facility)
    db.session.commit()
    
    flash(f'Instalación "{name}" eliminada permanentemente', 'success')
    return redirect(url_for('bookings.facilities_list'))

# ═══════════════════════════════════════════════════════
# APROBAR / RECHAZAR RESERVAS
# ═══════════════════════════════════════════════════════

@bp.route('/<int:booking_id>/approve', methods=['POST'])
@login_required
@require_permission('bookings', level=2)
def approve(booking_id):
    """Aprobar una reserva pendiente"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.status != 'pending':
        flash('Solo se pueden aprobar reservas pendientes', 'warning')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    booking.status = 'approved'
    booking.approved_by_id = current_user.id
    booking.approved_at = datetime.utcnow()
    
    db.session.commit()
    
    flash(f'Reserva #{booking.id} aprobada exitosamente', 'success')
    return redirect(url_for('bookings.detail', booking_id=booking_id))


@bp.route('/<int:booking_id>/reject', methods=['POST'])
@login_required
@require_permission('bookings', level=2)
def reject(booking_id):
    """Rechazar una reserva pendiente"""
    booking = Booking.query.get_or_404(booking_id)
    
    if booking.status != 'pending':
        flash('Solo se pueden rechazar reservas pendientes', 'warning')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    booking.status = 'rejected'
    booking.approved_by_id = current_user.id
    booking.approved_at = datetime.utcnow()
    booking.rejection_reason = request.form.get('rejection_reason', '').strip()
    
    db.session.commit()
    
    flash(f'Reserva #{booking.id} rechazada', 'info')
    return redirect(url_for('bookings.detail', booking_id=booking_id))