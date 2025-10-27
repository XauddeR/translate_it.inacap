import os
from flask import Blueprint, render_template, abort, send_from_directory, flash, redirect, url_for, send_file, request, current_app
from werkzeug.utils import secure_filename
from MySQLdb.cursors import DictCursor
from flask_login import current_user, login_required
from utils.extensions import mysql
from io import BytesIO

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/support')
@login_required
def support():
    return render_template('support.html', user = current_user)

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

@main_bp.route('/archivo/<archivo_id>')
@login_required
def file_detail(archivo_id):
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute('SELECT * FROM ARCHIVOS WHERE id = %s', (archivo_id,))
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

@main_bp.route('/archivo/thumbnail/<filename>')
@login_required
def file_thumbnail(filename):
    safe_filename = secure_filename(filename)
    thumbnail_folder = os.path.join(current_app.root_path, 'uploads', 'thumbnail')
    file_path = os.path.join(thumbnail_folder, safe_filename)

    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(thumbnail_folder, safe_filename, as_attachment = False)


@main_bp.route('/update_file/<archivo_id>', methods=['POST'])
@login_required
def update_file(archivo_id):
    nuevo_nombre = request.form['filename']
    cursor = mysql.connection.cursor()
    cursor.execute(
        '''
        UPDATE archivos 
        SET nombre_archivo = %s 
        WHERE id = %s AND usuario_id = %s
        ''',
        (nuevo_nombre, archivo_id, current_user.id)
    )
    mysql.connection.commit()
    cursor.close()

    flash('Título del archivo actualizado correctamente.', 'update_success')
    return redirect(url_for('main.history'))

@main_bp.route('/delete_file/<archivo_id>', methods=['POST'])
@login_required
def delete_file(archivo_id):
    cursor = mysql.connection.cursor()
    cursor.execute(
        'DELETE FROM archivos WHERE id = %s AND usuario_id = %s',
        (archivo_id, current_user.id)
    )
    mysql.connection.commit()
    cursor.close()
    flash('Archivo eliminado del historial.', 'delete_success')
    return redirect(url_for('main.history'))

@main_bp.route('/download/<archivo_id>')
@login_required
def download(archivo_id):
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute(
        '''
        SELECT traduccion, nombre_archivo, filename, usuario_id FROM archivos WHERE id = %s
        ''',
        (archivo_id,)
    )
    archivo = cursor.fetchone()
    cursor.close()

    if not archivo:
        abort(404, 'Archivo no encontrado.')

    if archivo['usuario_id'] != current_user.id:
        abort(403, 'No tienes permiso para descargar este archivo.')

    nombre = archivo['nombre_archivo'] or archivo['filename']
    nombre_txt = f'{nombre.rsplit('.', 1)[0]}_traduccion.txt'

    buffer = BytesIO()
    buffer.write(archivo['traduccion'].encode('utf-8'))
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment = True,
        download_name = nombre_txt,
        mimetype = 'text/plain'
    )