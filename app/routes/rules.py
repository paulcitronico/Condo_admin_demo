from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('rules', __name__, url_prefix='/rules')

@bp.route('/')
@login_required
def index():
    # Si es solo info estática, puedes pasar datos si los necesitas
    return render_template('rules/index.html')