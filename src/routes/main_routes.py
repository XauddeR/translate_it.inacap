import os
from flask import Blueprint, render_template, abort, send_from_directory, current_app
from werkzeug.utils import secure_filename
from MySQLdb.cursors import DictCursor
from flask_login import current_user, login_required
from utils.extensions import mysql

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user = current_user)

@main_bp.route('/historial')
@login_required
def history():
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute('SELECT * FROM ARCHIVOS WHERE USUARIO_ID = %s ORDER BY FECHA_SUBIDA DESC', (current_user.id,))
    archivos = cursor.fetchall()
    cursor.close()

    return render_template('history.html', archivos = archivos)

@main_bp.route('/archivo/<int:archivo_id>')
@login_required
def file_detail(archivo_id):
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute('SELECT * FROM ARCHIVOS WHERE id=%s', (archivo_id,))
    archivo = cursor.fetchone()
    cursor.close()

    if not archivo:
        abort(404)
    if archivo['usuario_id'] != current_user.id:
        abort(403)

    return render_template('file_detail.html', archivo = archivo)

@main_bp.route('/archivo/video/<filename>')
@login_required
def file_video(filename):
    safe_filename = secure_filename(filename)
    upload_folder = os.path.join(current_app.root_path, 'uploads', 'videos')
    file_path = os.path.join(upload_folder, safe_filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(upload_folder, safe_filename, as_attachment = False)


