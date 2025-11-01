from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
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
    cursor.close()
    return render_template('admin/admin_dashboard.html', total_users = total_users, total_admins = total_admins, total_archivos = total_archivos, idiomas = idiomas)

# Visualización de todos los usuarios registrados en el sistema
@admin_bp.route('/view-users')
@login_required
@admin_required
def view_users():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT u.id, u.usuario, u.email,
               CASE WHEN a.id IS NULL THEN 0 ELSE 1 END AS is_admin
        FROM usuarios u
        LEFT JOIN administradores a ON a.usuario_id = u.id
        ORDER BY u.fecha_registro ASC
    """)
    users = cursor.fetchall()
    cursor.close()
    return render_template('admin/view_user.html', users = users)

# Funcionalidad para eliminar usuarios según ID registrado en la base de datos
@admin_bp.route('/delete/<int:user_id>', methods = ['POST'])
@login_required
@admin_required
def delete_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute('DELETE FROM usuarios WHERE id = %s', (user_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Usuario eliminado correctamente', 'delete_success')
    return redirect(url_for('admin.view_users'))

# Funcionalidad para modificar datos de usuario según ID registrada en la base de datos
@admin_bp.route('/update/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def update_user(user_id):
    cursor = mysql.connection.cursor()

    if request.method == 'POST':
        usuario  = (request.form.get('usuario') or '').strip()
        email    = (request.form.get('email') or '').strip()
        password = (request.form.get('password') or '').strip()
        nivel    = (request.form.get('nivel') or 'usuario').strip().lower()

        if not usuario or not email:
            cursor.close()
            flash('Usuario y correo son obligatorios.', 'update_error')
            return redirect(url_for('admin.view_users'))

        if password:
            hashed = generate_password_hash(password)
            cursor.execute("""
                UPDATE usuarios
                SET usuario=%s, email=%s, password_bcrypt=%s
                WHERE id=%s
            """, (usuario, email, hashed, user_id))
        else:
            cursor.execute("""
                UPDATE usuarios
                SET usuario=%s, email=%s
                WHERE id=%s
            """, (usuario, email, user_id))

        cursor.execute("SELECT id FROM administradores WHERE usuario_id=%s", (user_id,))
        admin_row = cursor.fetchone()

        if nivel == 'admin' and not admin_row:
            cursor.execute("""
                INSERT INTO administradores (usuario_id, nivel_acceso)
                VALUES (%s, %s)
            """, (user_id, 'admin'))
        elif nivel != 'admin' and admin_row:
            cursor.execute("DELETE FROM administradores WHERE usuario_id=%s", (user_id,))

        mysql.connection.commit()
        cursor.close()

        flash('Usuario actualizado correctamente.', 'update_success')
        return redirect(url_for('admin.view_users'))

    cursor.close()
    return redirect(url_for('admin.view_users'))


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

@admin_bp.route('/support')
@login_required
@admin_required
def support_list():
    estado = request.args.get('estado', '').strip().lower()
    q = request.args.get('q', '').strip()

    where = []
    params = []

    if estado:
        where.append("t.estado = %s")
        params.append(estado)

    if q:
        where.append("(t.asunto LIKE %s OR u.usuario LIKE %s OR u.email LIKE %s)")
        like = f"%{q}%"
        params.extend([like, like, like])

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    sql = f"""
        SELECT
            t.id, t.asunto, t.estado, t.creado_en, t.actualizado_en,
            u.id AS usuario_id, u.usuario, u.email
        FROM tickets t
        JOIN usuarios u ON u.id = t.usuario_id
        {where_sql}
        ORDER BY COALESCE(t.actualizado_en, t.creado_en) DESC
    """

    cur = mysql.connection.cursor()
    cur.execute(sql, params)
    tickets = cur.fetchall()
    cur.close()

    return render_template('admin/support_list.html', tickets = tickets, estado = estado, q=q)

@admin_bp.route('/support/<int:ticket_id>')
@login_required
@admin_required
def support_ticket_detail(ticket_id):
    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT t.id, t.usuario_id, t.asunto, t.estado, t.creado_en, t.actualizado_en,
               u.usuario AS usuario_nombre, u.email AS usuario_email
        FROM tickets t
        JOIN usuarios u ON u.id = t.usuario_id
        WHERE t.id = %s
        LIMIT 1
    """, (ticket_id,))
    ticket = cur.fetchone()
    if not ticket:
        cur.close()
        flash("El ticket no existe.", "error")
        return redirect(url_for('admin.support_list'))

    cur.execute("""
        SELECT id, ticket_id, autor_usuario_id, autor_admin_id, mensaje, creado_en
        FROM ticket_mensajes
        WHERE ticket_id = %s
        ORDER BY creado_en ASC
    """, (ticket_id,))
    mensajes = cur.fetchall()
    cur.close()

    return render_template('admin/support_ticket.html', ticket = ticket, mensajes = mensajes)

@admin_bp.post('/support/tickets/<int:ticket_id>/reply', endpoint='support_ticket_reply')
@admin_required
def support_ticket_reply(ticket_id):
    mensaje = (request.form.get('message') or '').strip()
    if not mensaje:
        flash('El mensaje no puede estar vacío.', 'error')
        return redirect(url_for('admin.support_ticket_detail', ticket_id=ticket_id))

    cur = mysql.connection.cursor()

    # 0) Verificar ticket existe (opcional pero sano)
    cur.execute("SELECT id, estado FROM tickets WHERE id = %s", (ticket_id,))
    tk = cur.fetchone()
    if not tk:
        cur.close()
        abort(404)

    # 1) Obtener el ID REAL del admin en la tabla administradores
    cur.execute("SELECT id FROM administradores WHERE usuario_id = %s", (current_user.id,))
    admin = cur.fetchone()
    if not admin:
        cur.close()
        abort(403)  # el usuario no figura como admin en la tabla administradores

    admin_id = admin['id']

    # 2) Insertar mensaje (autor_usuario_id debe ir NULL)
    cur.execute("""
        INSERT INTO ticket_mensajes (ticket_id, autor_usuario_id, autor_admin_id, mensaje)
        VALUES (%s, %s, %s, %s)
    """, (ticket_id, None, admin_id, mensaje))

    # 3) Actualizar estado/fecha del ticket si lo deseas
    cur.execute("""
        UPDATE tickets
        SET actualizado_en = NOW(),
            estado = CASE WHEN estado = 'abierto' THEN 'pendiente' ELSE estado END
        WHERE id = %s
    """, (ticket_id,))

    mysql.connection.commit()
    cur.close()

    flash('Respuesta enviada.', 'success')
    return redirect(url_for('admin.support_ticket_detail', ticket_id=ticket_id))

@admin_bp.post('/support/tickets/<int:ticket_id>/status', endpoint = 'support_ticket_set_status')
@admin_required
def support_ticket_set_status(ticket_id):
    estado = (request.form.get('estado') or '').strip().lower()
    permitidos = {'abierto', 'pendiente', 'resuelto', 'cerrado'}
    if estado not in permitidos:
        flash('Estado inválido.', 'error')
        return redirect(url_for('admin.support_ticket_detail', ticket_id = ticket_id))

    cur = mysql.connection.cursor()

    cur.execute("SELECT id FROM tickets WHERE id = %s", (ticket_id,))
    if not cur.fetchone():
        cur.close()
        abort(404)

    cur.execute("""
        UPDATE tickets
        SET estado = %s,
            actualizado_en = NOW()
        WHERE id = %s
    """, (estado, ticket_id))

    mysql.connection.commit()
    cur.close()

    flash(f"Estado actualizado a {estado}.", "success")
    return redirect(url_for('admin.support_ticket_detail', ticket_id=ticket_id))
