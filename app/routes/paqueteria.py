# app/routes/paqueteria.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.paqueteria import Paqueteria
from datetime import datetime

# Asumiendo que usas un decorador de permisos similar al de parking
# from app.utils.decorators import require_permission 

bp = Blueprint('paqueteria', __name__, url_prefix='/paqueteria')

@bp.route('/')
@login_required
# @require_permission('paqueteria', level=2) # Descomenta y ajusta según tu sistema de roles
def index():
    # Paquetes esperando a ser retirados
    pendientes = Paqueteria.query.filter_by(hora_retiro=None).order_by(Paqueteria.hora_llegada.desc()).all()
    
    # Historial de los últimos 50 paquetes ya entregados
    entregados = Paqueteria.query.filter(Paqueteria.hora_retiro != None).order_by(Paqueteria.hora_retiro.desc()).limit(50).all()
    
    return render_template('paqueteria/index.html', pendientes=pendientes, entregados=entregados)


@bp.route('/llegada', methods=['POST'])
@login_required
def registrar_llegada():
    """El guardia registra que llegó un paquete de un proveedor."""
    proveedor = request.form.get('proveedor_paquete', '').strip()
    destinatario = request.form.get('destinatario', '').strip()
    tipo = request.form.get('tipo', 'No frágil')
    
    if not proveedor or not destinatario:
        flash('El proveedor y el destinatario son obligatorios.', 'danger')
        return redirect(url_for('paqueteria.index'))
        
    nuevo_paquete = Paqueteria(
        proveedor_paquete=proveedor,
        destinatario=destinatario,
        tipo=tipo,
        recibido_por_id=current_user.id
    )
    
    db.session.add(nuevo_paquete)
    db.session.commit()
    flash('Paquete registrado exitosamente.', 'success')
    return redirect(url_for('paqueteria.index'))


@bp.route('/retiro/<int:paquete_id>', methods=['POST']) # Sin slash al final
@login_required
def registrar_retiro(paquete_id):
    """El guardia registra a quién se le entregó el paquete y guarda la firma."""
    paquete = Paqueteria.query.get_or_404(paquete_id)
    
    if paquete.hora_retiro:
        flash('Este paquete ya fue entregado.', 'warning')
        return redirect(url_for('paqueteria.index'))
        
    persona_retira = request.form.get('persona_retira', '').strip()
    firma_base64 = request.form.get('firma_data') # Esto lo enviaremos desde el JS del HTML
    
    if not persona_retira:
        flash('Debe indicar quién retira el paquete.', 'danger')
        return redirect(url_for('paqueteria.index'))
        
    paquete.persona_retira = persona_retira
    paquete.firma = firma_base64
    paquete.hora_retiro = datetime.utcnow()
    paquete.entregado_por_id = current_user.id
    
    db.session.commit()
    flash('Paquete entregado correctamente.', 'success')
    return redirect(url_for('paqueteria.index'))