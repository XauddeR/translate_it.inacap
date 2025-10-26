from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from MySQLdb.cursors import DictCursor
from werkzeug.security import generate_password_hash
from functools import wraps
from utils.extensions import mysql

admin_bp = Blueprint('admin', __name__)

def admin_required(func):
    @wraps(func)
    def view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    return view

@admin_bp.route('/admin-dashboard')
@login_required
@admin_required
def admin_dashboard():
    cursor = mysql.connection.cursor(DictCursor)

    cursor.execute('SELECT COUNT(*) AS TOTAL_USUARIOS FROM USUARIOS')
    total_users = cursor.fetchone()['TOTAL_USUARIOS']

    cursor.execute('SELECT COUNT(*) AS TOTAL_ADMINS FROM administradores')
    total_admins = cursor.fetchone()['TOTAL_ADMINS']
    
    cursor.execute('SELECT COUNT(*) AS TOTAL_ARCHIVOS FROM ARCHIVOS')
    total_archivos = cursor.fetchone()['TOTAL_ARCHIVOS']

    cursor.execute('''
        SELECT idioma_destino, COUNT(*) as cantidad 
        FROM ARCHIVOS 
        GROUP BY idioma_destino 
        ORDER BY cantidad DESC 
        LIMIT 5
    ''')
    idiomas = cursor.fetchall()
    cursor.close()
    return render_template('admin/admin_dashboard.html', total_users = total_users, total_admins = total_admins, total_archivos = total_archivos, idiomas = idiomas)

# Apartado para visualizar todos los usuarios registrados en el sistema
@admin_bp.route('/view-users')
@login_required
@admin_required
def view_users():
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute('SELECT ID, USUARIO, EMAIL FROM USUARIOS ORDER BY FECHA_REGISTRO ASC')
    users = cursor.fetchall()
    cursor.close()
    return render_template('admin/view_user.html', users = users)

# Funcionalidad para eliminar usuarios según ID registrado en la base de datos
@admin_bp.route('/delete/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    cursor = mysql.connection.cursor(DictCursor)
    cursor.execute('DELETE FROM USUARIOS WHERE ID = %s', (user_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Usuario eliminado correctamente', 'delete_success')
    return redirect(url_for('admin.view_users'))

# Funcionalidad para modificar datos de usuario según ID registrada en la base de datos
@admin_bp.route('/update/<int:user_id>', methods = ['GET', 'POST'])
@login_required
@admin_required
def update_user(user_id):
    cursor = mysql.connection.cursor(DictCursor)
    if request.method == 'POST':
        user = request.form['usuario']
        email = request.form['email']
        cursor.execute('UPDATE USUARIOS SET USUARIO = %s, EMAIL = %s WHERE ID = %s', (user, email, user_id))
        mysql.connection.commit()
        cursor.close()
        flash('Usuario actualizado correctamente', 'update_success')
        return redirect(url_for('admin.view_users'))
    else:
        cursor.execute('SELECT ID, USUARIO, EMAIL FROM USUARIOS WHERE ID = %s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return render_template('admin/update_user.html', user = user)

# Funcionalidad para crear un usuario desde panel de administrador
@admin_bp.route('/add', methods = ['POST'])
@login_required
@admin_required
def add_user():
    usuario = request.form['usuario']
    email = request.form['email']
    password = request.form['password']
    nivel = request.form['nivel']
    hashed_password = generate_password_hash(password)

    try:
        cursor = mysql.connection.cursor()
        cursor.execute('''
            INSERT INTO usuarios (usuario, email, password_bcrypt)
            VALUES (%s, %s, %s)
        ''', (usuario, email, hashed_password))
        mysql.connection.commit()

        cursor.execute('SELECT LAST_INSERT_ID()')
        usuario_id = cursor.fetchone()[0]

        if nivel == 'admin':
            cursor.execute('''
                INSERT INTO administradores (usuario_id, nivel_acceso)
                VALUES (%s, %s)
            ''', (usuario_id, 'admin'))
            mysql.connection.commit()

        cursor.close()
        flash('Usuario creado exitosamente.', 'add_success')

    except Exception as e:
        flash(f'Error al crear usuario: {str(e)}', 'add_user_error')

    return redirect(url_for('admin.view_users'))


