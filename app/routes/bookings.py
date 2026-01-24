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
