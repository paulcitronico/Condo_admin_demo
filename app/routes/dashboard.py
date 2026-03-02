from flask import Blueprint, render_template
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import func
from app import db
from app.models import *

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    # Datos del dashboard usando las funciones auxiliares
    upcoming_bookings = get_upcoming_bookings()
    parking_stats = get_parking_stats()
    recent_announcements = get_recent_announcements()
    financial_stats = get_financial_stats()
    roles_summary = get_roles_summary()

    return render_template('dashboard/index.html', 
                           upcoming_bookings=upcoming_bookings,
                           parking_stats=parking_stats,
                           recent_announcements=recent_announcements,
                           financial_stats=financial_stats,
                           roles_summary=roles_summary)


def get_financial_stats():
    """Obtiene estadísticas financieras totales e históricas"""
    if not current_user.can_read('financials'):
        return None
    
    # ELIMINAMOS el filtro de mes y año actual para que cuente todo lo registrado
    total_collected = db.session.query(func.sum(FinancialTransaction.amount)).filter(
        FinancialTransaction.transaction_type == 'payment',
        FinancialTransaction.status == 'completed'
    ).scalar() or 0
    
    # Balance pendiente total (se mantiene igual según tu preferencia)
    total_pending = db.session.query(func.sum(FinancialAccount.total_owed - FinancialAccount.total_paid)).filter(
        FinancialAccount.total_owed > FinancialAccount.total_paid
    ).scalar() or 0
    
    # Total de cuentas
    total_accounts = FinancialAccount.query.count()
    
    # Cuentas al día
    accounts_paid = FinancialAccount.query.filter_by(status='current').count()
    
    collection_progress = (accounts_paid / total_accounts * 100) if total_accounts > 0 else 0
    
    return {
        'total_collected': float(total_collected),
        'total_pending': float(total_pending),
        'total_accounts': total_accounts,
        'accounts_paid': accounts_paid,
        'collection_progress': collection_progress
    }


def get_upcoming_bookings():
    """Obtiene próximas reservas"""
    if not current_user.can_read('bookings'):
        return []
    
    today = datetime.now().date()
    next_week = today + timedelta(days=7)
    
    bookings = Booking.query.filter(
        Booking.booking_date >= today,
        Booking.booking_date <= next_week,
        Booking.status.in_(['pending', 'approved'])
    ).order_by(Booking.booking_date, Booking.start_time).limit(5).all()
    
    return bookings


def get_parking_stats():
    """Obtiene estadísticas de estacionamientos"""
    if not current_user.can_read('parking'):
        return None
    
    total_spots = ParkingSpot.query.filter_by(is_active=True).count()
    occupied = ParkingSpot.query.filter_by(status='occupied', is_active=True).count()
    available = ParkingSpot.query.filter_by(status='available', is_active=True).count()
    reserved = ParkingSpot.query.filter_by(status='reserved', is_active=True).count()
    
    return {
        'total': total_spots,
        'occupied': occupied,
        'available': available,
        'reserved': reserved,
        'occupancy_rate': (occupied / total_spots * 100) if total_spots > 0 else 0
    }


def get_recent_announcements():
    """Obtiene anuncios recientes"""
    if not current_user.can_read('announcements'):
        return []
    
    announcements = Announcement.query.filter_by(is_published=True).order_by(
        Announcement.created_at.desc()
    ).limit(3).all()
    
    return announcements


def get_roles_summary():
    """Obtiene resumen de roles"""
    if not current_user.can_read('roles'):
        return None
    
    roles = Role.query.filter_by(is_active=True).all()
    
    summary = []
    for role in roles:
        user_count = User.query.filter_by(role_id=role.id, is_active=True).count()
        summary.append({
            'role': role,
            'user_count': user_count
        })
    
    return summary