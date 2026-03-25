from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from ..models.comprobantes import Comprobante
from .. import db
import os
from PIL import Image
from datetime import datetime

bp = Blueprint('comprobante', __name__, url_prefix='/comprobante')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_optimized_image(file, upload_folder):
    img = Image.open(file)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    
    max_width = 1200
    if img.width > max_width:
        ratio = max_width / float(img.width)
        height = int(float(img.height) * float(ratio))
        img = img.resize((max_width, height), Image.Resampling.LANCZOS)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recibo_{current_user.id}_{timestamp}.jpg"
    save_path = os.path.join(upload_folder, filename)
    
    img.save(save_path, "JPEG", optimize=True, quality=75)
    return filename

@bp.route('/')
@login_required
def index():
    privileged_roles = ['super_admin', 'administrator', 'board_member']
    is_admin = current_user.role.name in privileged_roles
    
    if is_admin:
        receipts = Comprobante.query.order_by(Comprobante.created_at.desc()).all()
    else:
        receipts = Comprobante.query.filter_by(user_id=current_user.id).order_by(Comprobante.created_at.desc()).all()

    return render_template('comprobante/index.html', is_admin=is_admin, receipts=receipts)

@bp.route('/subir', methods=['POST'])
@login_required
def upload_receipt():
    if 'receipt_image' not in request.files:
        flash('No se seleccionó ninguna imagen', 'error')
        return redirect(request.url)
    
    file = request.files['receipt_image']
    amount = request.form.get('amount')
    p_date = request.form.get('payment_date')

    if file and allowed_file(file.filename) and amount and p_date:
        folder = os.path.join(current_app.root_path, 'static', 'uploads', 'receipts')
        if not os.path.exists(folder):
            os.makedirs(folder)

        try:
            filename = save_optimized_image(file, folder)
            
            nuevo_pago = Comprobante(
                amount=float(amount),
                payment_date=datetime.strptime(p_date, '%Y-%m-%d').date(),
                filename=filename,
                user_id=current_user.id
            )
            db.session.add(nuevo_pago)
            db.session.commit()

            flash('Comprobante enviado correctamente', 'success')
            return redirect(url_for('comprobante.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al procesar: {str(e)}', 'error')
            return redirect(request.url)
    
    flash('Datos incompletos o formato no permitido', 'error')
    return redirect(request.url)