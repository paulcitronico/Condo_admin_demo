import smtplib
from email.mime.text import MIMEText
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.announcement import Announcement, AnnouncementAcknowledgment
from app.models.user import User
from app.routes.roles import require_permission

bp = Blueprint('announcements', __name__, url_prefix='/announcements')


def build_announcement_email_content(announcement):
    base_url = "https://jl2flq77-5000.brs.devtunnels.ms"
    path = url_for('announcements.detail', announcement_id=announcement.id)
    announcement_url = f"{base_url}{path}"

    subject = f"📢 Nuevo comunicado: {announcement.title}"

    body = (
        f"Hola,\n\n"
        f"Se publicó un nuevo comunicado en la comunidad.\n\n"
        f"📢 Título: {announcement.title}\n"
        f"📌 Prioridad: {(announcement.priority or 'normal').upper()}\n"
        f"📂 Categoría: {announcement.category or 'General'}\n"
        f"📅 Fecha: {announcement.created_at.strftime('%d/%m/%Y %H:%M')}\n\n"
        f"Puedes revisarlo completo aquí:\n"
        f"{announcement_url}\n\n"
        f"Saludos cordiales,\n"
        f"Administración"
    )

    return subject, body


def send_mass_announcement_email(announcement, recipients):
    """
    Envía correo masivo a una lista de usuarios
    """
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SMTP_USER = "tu.correo@gmail.com"
    SMTP_PASS = "tu_clave_de_aplicacion"

    subject, body = build_announcement_email_content(announcement)

    sent = 0
    failed = 0
    errors = []

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)

        for user in recipients:
            try:
                msg = MIMEText(body, _charset="utf-8")
                msg["Subject"] = subject
                msg["From"] = SMTP_USER
                msg["To"] = user.email

                server.send_message(msg)
                sent += 1
            except Exception as e:
                failed += 1
                errors.append(f"{user.full_name} ({user.email}): {str(e)}")

        server.quit()

    except Exception as e:
        return {
            "success": False,
            "sent": sent,
            "failed": len(recipients),
            "errors": [str(e)]
        }

    return {
        "success": True,
        "sent": sent,
        "failed": failed,
        "errors": errors
    }


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
    
    announcement.acknowledge_by(current_user)
    db.session.commit()
    
    stats = None
    email_recipients = []

    if current_user.can_write('announcements'):
        stats = announcement.get_acknowledgment_stats()

        email_recipients = User.query.filter(
            User.is_active.is_(True),
            User.email.isnot(None),
            User.email != ''
        ).order_by(User.last_name, User.first_name).all()
    
    return render_template(
        'announcements/detail.html',
        announcement=announcement,
        stats=stats,
        email_recipients=email_recipients
    )


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
        
        expiry_date_str = request.form.get('expiry_date')
        if expiry_date_str:
            announcement.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d')
        
        db.session.add(announcement)
        db.session.commit()
        
        flash('Anuncio creado exitosamente', 'success')
        return redirect(url_for('announcements.detail', announcement_id=announcement.id))
    
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


@bp.route('/<int:announcement_id>/email-preview', methods=['GET', 'POST'])
@login_required
@require_permission('announcements', level=2)
def email_preview(announcement_id):
    """Vista intermedia para previsualizar y seleccionar destinatarios"""
    announcement = Announcement.query.get_or_404(announcement_id)

    if request.method == 'POST':
        selected_users = request.form.getlist('selected_users', type=int)

        if not selected_users:
            flash('Debes seleccionar al menos un destinatario.', 'warning')
            return redirect(url_for('announcements.email_preview', announcement_id=announcement.id))

        recipients = User.query.filter(
            User.id.in_(selected_users),
            User.is_active.is_(True),
            User.email.isnot(None)
        ).order_by(User.last_name, User.first_name).all()

        result = send_mass_announcement_email(announcement, recipients)

        if result["success"]:
            flash(
                f'Correos enviados correctamente. Enviados: {result["sent"]}, Fallidos: {result["failed"]}.',
                'success'
            )
        else:
            flash(
                f'Error al enviar correos. Detalle: {", ".join(result["errors"][:5])}',
                'error'
            )

        return redirect(url_for('announcements.detail', announcement_id=announcement.id))

    recipients = User.query.filter(
        User.is_active.is_(True),
        User.email.isnot(None),
        User.email != ''
    ).order_by(User.last_name, User.first_name).all()

    subject, body = build_announcement_email_content(announcement)

    return render_template(
        'announcements/email_batch.html',
        announcement=announcement,
        recipients=recipients,
        subject=subject,
        body=body
    )


@bp.route('/<int:announcement_id>/send-email', methods=['POST'])
@login_required
@require_permission('announcements', level=2)
def send_email_batch(announcement_id):
    """Endpoint extra por si se quiere usar de otra forma"""
    return redirect(url_for('announcements.email_preview', announcement_id=announcement_id))