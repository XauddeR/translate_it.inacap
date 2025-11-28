from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, timezone
from functools import wraps
from utils.languages_dao import get_lang, add_lang, enable_lang, disable_lang
from utils.extensions import mysql

admin_bp = Blueprint('admin', __name__)

def admin_required(func):
    @wraps(func)
    def view(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    return view

# Contadores principales del dashboard administrador
@admin_bp.route('/admin-dashboard')
@login_required
@admin_required
def admin_dashboard():
    cursor = mysql.connection.cursor()

    cursor.execute('SELECT COUNT(*) AS TOTAL_USUARIOS FROM usuarios')
    total_users = cursor.fetchone()['TOTAL_USUARIOS']

    cursor.execute('SELECT COUNT(*) AS TOTAL_ADMINS FROM administradores')
    total_admins = cursor.fetchone()['TOTAL_ADMINS']
    
    cursor.execute('SELECT COUNT(*) AS TOTAL_ARCHIVOS FROM archivos')
    total_archivos = cursor.fetchone()['TOTAL_ARCHIVOS']

    cursor.execute('''
        SELECT idioma_destino, COUNT(*) as cantidad 
        FROM archivos 
        GROUP BY idioma_destino 
        ORDER BY cantidad DESC 
        LIMIT 5
    ''')
    idiomas = cursor.fetchall()

    today = datetime.now(timezone.utc).date()
    ago_30 = today - timedelta(days = 29)

    cursor.execute('''
        SELECT DATE(fecha_registro) AS fecha, COUNT(*) AS cantidad
        FROM usuarios
        WHERE fecha_registro >= %s
        GROUP BY DATE(fecha_registro)
        ORDER BY fecha ASC
    ''', (ago_30,))
    rows = cursor.fetchall()
    cursor.close()

    counts_by_day = {row['fecha']: row['cantidad'] for row in rows}

    labels = []
    values = []
    for i in range(30):
        fecha = ago_30 + timedelta(days = i)
        labels.append(fecha.strftime('%d/%m'))
        values.append(counts_by_day.get(fecha, 0))    

    cursor.close()
    return render_template('admin/admin_dashboard.html', 
                           total_users = total_users, 
                           total_admins = total_admins, 
                           total_archivos = total_archivos, 
                           idiomas = idiomas,
                           daily_labels = labels,
                           daily_values = values)

# Visualización de todos los usuarios registrados en el sistema
@admin_bp.route('/view-users')
@login_required
@admin_required
def view_users():
    q = (request.args.get('q') or '').strip()
    filtro = (request.args.get('filtro') or '').strip()
    rol = (request.args.get('rol') or '').strip()

    where = []
    params = []

    if q:
        if filtro == 'id':
            if q.isdigit():
                where.append('u.id = %s')
                params.append(int(q))
            else:
                where.append('1 = 0')
        elif filtro == 'usuario':
            where.append('u.usuario LIKE %s')
            params.append(f'%{q}%')
        elif filtro == 'email':
            where.append('u.email LIKE %s')
            params.append(f'%{q}%')
        else:
            like = f'%{q}%'
            where.append('(u.usuario LIKE %s OR u.email LIKE %s OR CAST(u.id AS CHAR) LIKE %s)')
            params.extend([like, like, like])

    if rol == 'admin':
        where.append('a.id IS NOT NULL')
    elif rol == 'usuario':
        where.append('a.id IS NULL')

    where_sql = 'WHERE ' + ' AND '.join(where) if where else ''

    cursor = mysql.connection.cursor()
    cursor.execute(f'''
        SELECT 
            u.id,
            u.usuario,
            u.email,
            CASE WHEN a.id IS NULL THEN 0 ELSE 1 END AS is_admin
        FROM usuarios u
        LEFT JOIN administradores a ON a.usuario_id = u.id
        {where_sql}
        ORDER BY u.fecha_registro ASC
    ''', params)
    users = cursor.fetchall()
    cursor.close()

    return render_template(
        'admin/view_user.html',
        users = users,
        q = q,
        filtro = filtro,
        rol = rol,
    )

# Eliminar usuarios según ID
@admin_bp.route('/delete/<int:user_id>', methods = ['POST'])
@login_required
@admin_required
def delete_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM usuarios WHERE id = %s', (user_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Usuario eliminado correctamente', 'admin_user_success')
    return redirect(url_for('admin.view_users'))

# Modificación de datos usuario según ID
@admin_bp.route('/update/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_user(user_id):
    cursor = mysql.connection.cursor()
    if request.method == 'POST':
        usuario = (request.form.get('usuario') or '').strip()
        email = (request.form.get('email') or '').strip()
        nivel = (request.form.get('nivel') or 'usuario').strip().lower()

        try:
            if not usuario or not email:
                cursor.close()
                flash('Usuario y correo son obligatorios.', 'admin_user_error')
                return redirect(url_for('admin.view_users'))
            else:
                cursor.execute('''
                    UPDATE usuarios
                    SET usuario=%s, email=%s
                    WHERE id=%s
                ''', (usuario, email, user_id))

            cursor.execute('SELECT id FROM administradores WHERE usuario_id = %s', (user_id,))
            admin_row = cursor.fetchone()

            if nivel == 'admin' and not admin_row:
                cursor.execute('''
                    INSERT INTO administradores (usuario_id, nivel_acceso)
                    VALUES (%s, %s)
                ''', (user_id, 'admin'))
            elif nivel != 'admin' and admin_row:
                cursor.execute('DELETE FROM administradores WHERE usuario_id = %s', (user_id,))

            mysql.connection.commit()
            cursor.close()

            flash('Usuario actualizado correctamente.', 'admin_user_success')
            return redirect(url_for('admin.view_users'))
        except Exception as e:
            flash(f'Error al actualizar usuario: {str(e)}', 'admin_user_error')
    return redirect(url_for('admin.view_users'))

# Funcionalidad para crear un usuario desde panel de administrador
@admin_bp.route('/add-user', methods = ['POST'])
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

        usuario_id = cursor.lastrowid

        if nivel == 'admin':
            cursor.execute('''
                INSERT INTO administradores (usuario_id, nivel_acceso)
                VALUES (%s, %s)
            ''', (usuario_id, 'admin'))
            mysql.connection.commit()

        cursor.close()
        flash('Usuario creado exitosamente.', 'admin_user_success')

    except Exception as e:
        flash(f'Error al crear usuario: {str(e)}', 'admin_user_error')

    return redirect(url_for('admin.view_users'))

# Vista administrador de todos los tickets solicitados por usuarios.
@admin_bp.route('/support')
@login_required
@admin_required
def support_list():
    estado = request.args.get('estado', '').strip().lower()
    q = request.args.get('q', '').strip()

    where = []
    params = []

    if estado:
        where.append('t.estado = %s')
        params.append(estado)

    if q:
        where.append('(t.asunto LIKE %s OR u.usuario LIKE %s OR u.email LIKE %s)')
        like = f'%{q}%'
        params.extend([like, like, like])

    where_sql = ('WHERE ' + ' AND '.join(where)) if where else ''

    sql = f'''
        SELECT
            t.id, t.asunto, t.estado, t.creado_en, t.actualizado_en,
            u.id AS usuario_id, u.usuario, u.email
        FROM tickets t
        JOIN usuarios u ON u.id = t.usuario_id
        {where_sql}
        ORDER BY COALESCE(t.actualizado_en, t.creado_en) DESC
    '''

    cursor = mysql.connection.cursor()
    cursor.execute(sql, params)
    tickets = cursor.fetchall()
    cursor.close()

    return render_template('admin/support_list.html', tickets = tickets, estado = estado, q = q)

# Gestión de un ticket por ID.
@admin_bp.route('/support/<int:ticket_id>')
@login_required
@admin_required
def support_ticket_detail(ticket_id):
    cursor = mysql.connection.cursor()

    cursor.execute('''
        SELECT t.id, t.usuario_id, t.asunto, t.estado, t.creado_en, t.actualizado_en,
               u.usuario AS usuario_nombre, u.email AS usuario_email
        FROM tickets t
        JOIN usuarios u ON u.id = t.usuario_id
        WHERE t.id = %s
        LIMIT 1
    ''', (ticket_id,))
    ticket = cursor.fetchone()
    if not ticket:
        cursor.close()
        flash('El ticket no existe.', 'admin_ticket_error')
        return redirect(url_for('admin.support_list'))

    cursor.execute('''
        SELECT id, ticket_id, autor_usuario_id, autor_admin_id, mensaje, creado_en
        FROM ticket_mensajes
        WHERE ticket_id = %s
        ORDER BY creado_en ASC
    ''', (ticket_id,))
    mensajes = cursor.fetchall()
    cursor.close()

    return render_template('admin/support_ticket.html', ticket = ticket, mensajes = mensajes)

# Responder ticket.
@admin_bp.post('/support/tickets/<int:ticket_id>/reply', endpoint = 'support_ticket_reply')
@admin_required
def support_ticket_reply(ticket_id):
    mensaje = (request.form.get('message') or '').strip()
    if not mensaje:
        flash('El mensaje no puede estar vacío.', 'admin_ticket_error')
        return redirect(url_for('admin.support_ticket_detail', ticket_id=ticket_id))

    cursor = mysql.connection.cursor()

    cursor.execute('SELECT id, estado FROM tickets WHERE id = %s', (ticket_id,))
    tk = cursor.fetchone()
    if not tk:
        cursor.close()
        abort(404)

    cursor.execute('SELECT id FROM administradores WHERE usuario_id = %s', (current_user.id,))
    admin = cursor.fetchone()
    if not admin:
        cursor.close()
        abort(403)

    admin_id = admin['id']
    cursor.execute('''
        INSERT INTO ticket_mensajes (ticket_id, autor_usuario_id, autor_admin_id, mensaje)
        VALUES (%s, %s, %s, %s)
    ''', (ticket_id, None, admin_id, mensaje))

    cursor.execute('''
        UPDATE tickets
        SET actualizado_en = NOW(),
            estado = CASE WHEN estado = 'abierto' THEN 'pendiente' ELSE estado END
        WHERE id = %s
    ''', (ticket_id,))

    mysql.connection.commit()
    cursor.close()

    flash('Respuesta enviada.', 'admin_ticket_success')
    return redirect(url_for('admin.support_ticket_detail', ticket_id = ticket_id))

# Actualización de estado del ticket.
@admin_bp.post('/support/tickets/<int:ticket_id>/status', endpoint = 'support_ticket_set_status')
@admin_required
def support_ticket_set_status(ticket_id):
    estado = (request.form.get('estado') or '').strip().lower()
    permitidos = {'abierto', 'pendiente', 'resuelto', 'cerrado'}
    if estado not in permitidos:
        flash('Estado inválido.', 'admin_ticket_error')
        return redirect(url_for('admin.support_ticket_detail', ticket_id = ticket_id))

    cursor = mysql.connection.cursor()

    cursor.execute('SELECT id FROM tickets WHERE id = %s', (ticket_id,))
    if not cursor.fetchone():
        cursor.close()
        abort(404)

    cursor.execute('''
        UPDATE tickets
        SET estado = %s,
            actualizado_en = NOW()
        WHERE id = %s
    ''', (estado, ticket_id))

    mysql.connection.commit()
    cursor.close()

    flash(f'Estado actualizado a {estado}.', 'admin_ticket_success')
    return redirect(url_for('admin.support_ticket_detail', ticket_id = ticket_id))

# Gestión de idiomas disponibles.
@admin_bp.route('/languages', methods = ['GET'])
@login_required
@admin_required
def languages_list():
    languages = get_lang()
    return render_template('admin/languages_list.html', languages = languages)

# Añadir idioma por código [documentación DeepL].
@admin_bp.route('/add-language', methods = ['POST'])
@login_required
@admin_required
def create_language():
    name = request.form.get('name').strip()
    code = request.form.get('code').strip().upper()
    if not name or not code:
        flash('Nombre y código son obligatorios', 'language_error')
        return redirect(url_for('admin.languages_list'))
    try:
        add_lang(name, code)
        flash('Idioma agregado correctamente', 'language_success')
    except Exception as e:
        print(f'Error: {e}')
    return redirect(url_for('admin.languages_list'))

# Habilitar/deshabilitar idioma.
@admin_bp.route('/languages/<int:idioma_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_lang(idioma_id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('SELECT nombre FROM idiomas WHERE id = %s LIMIT 1', (idioma_id,))
        row = cursor.fetchone()
        cursor.close()

        nombre = row['nombre'] if row else 'Idioma'
        action = request.form.get('accion')

        if action == 'disable':
            disable_lang(idioma_id)
            flash(f'{nombre} fue deshabilitado.', 'language_warning')
        
        elif action == 'enable':
            enable_lang(idioma_id)
            flash(f'{nombre} fue habilitado.', 'language_success')
    except Exception as e:
        print(f'Error toggle: {e}')
        flash(f'Ha ocurrido un error inesperado')

    return redirect(url_for('admin.languages_list'))