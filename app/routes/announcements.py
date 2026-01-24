from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.announcement import Announcement, AnnouncementAcknowledgment
from app.routes.roles import require_permission

bp = Blueprint('announcements', __name__, url_prefix='/announcements')


@bp.route('/')
@login_required
@require_permission('announcements', level=1)
def index():
    """Lista de anuncios"""
    page = request.args.get('page', 1, type=int)
    priority_filter = request.args.get('priority', 'all')
    category_filter = request.args.get('category', 'all')
    
    query = Announcement.query.filter_by(is_published=True)
    
    if priority_filter != 'all':
        query = query.filter_by(priority=priority_filter)
    
    if category_filter != 'all':
        query = query.filter_by(category=category_filter)
    
    announcements = query.order_by(
        Announcement.created_at.desc()
    ).paginate(page=page, per_page=10, error_out=False)
    
    return render_template('announcements/index.html', announcements=announcements)


@bp.route('/<int:announcement_id>')
@login_required
@require_permission('announcements', level=1)
def detail(announcement_id):
    """Detalle de anuncio"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    # Marcar como leído
    announcement.acknowledge_by(current_user)
    db.session.commit()
    
    # Estadísticas de lectura (solo para admin)
    stats = None
    if current_user.can_write('announcements'):
        stats = announcement.get_acknowledgment_stats()
    
    return render_template('announcements/detail.html',
                         announcement=announcement,
                         stats=stats)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
@require_permission('announcements', level=2)
def create():
    """Crear nuevo anuncio"""
    if request.method == 'POST':
        announcement = Announcement(
            title=request.form.get('title'),
            content=request.form.get('content'),
            priority=request.form.get('priority', 'normal'),
            category=request.form.get('category'),
            affected_area=request.form.get('affected_area'),
            author_id=current_user.id,
            is_published=request.form.get('is_published') == 'on'
        )
        
        # Fecha de expiración (opcional)
        expiry_date_str = request.form.get('expiry_date')
        if expiry_date_str:
            announcement.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
        
        db.session.add(announcement)
        db.session.commit()
        
        flash('Anuncio creado exitosamente', 'success')
        return redirect(url_for('announcements.index'))
    
    return render_template('announcements/create.html')


@bp.route('/<int:announcement_id>/edit', methods=['GET', 'POST'])
@login_required
@require_permission('announcements', level=2)
def edit(announcement_id):
    """Editar anuncio"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    if request.method == 'POST':
        announcement.title = request.form.get('title')
        announcement.content = request.form.get('content')
        announcement.priority = request.form.get('priority')
        announcement.category = request.form.get('category')
        announcement.affected_area = request.form.get('affected_area')
        announcement.is_published = request.form.get('is_published') == 'on'
        
        expiry_date_str = request.form.get('expiry_date')
        if expiry_date_str:
            announcement.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
        else:
            announcement.expiry_date = None
        
        db.session.commit()
        
        flash('Anuncio actualizado exitosamente', 'success')
        return redirect(url_for('announcements.detail', announcement_id=announcement.id))
    
    return render_template('announcements/edit.html', announcement=announcement)


@bp.route('/<int:announcement_id>/delete', methods=['POST'])
@login_required
@require_permission('announcements', level=2)
def delete(announcement_id):
    """Eliminar anuncio"""
    announcement = Announcement.query.get_or_404(announcement_id)
    
    db.session.delete(announcement)
    db.session.commit()
    
    flash('Anuncio eliminado exitosamente', 'success')
    return redirect(url_for('announcements.index'))
