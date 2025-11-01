from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from utils.extensions import mysql

support_bp = Blueprint('support', __name__)

@support_bp.route('/', methods = ['GET'])
@login_required
def support_home():
    cursor = mysql.connection.cursor()
    cursor.execute('''
        SELECT id, asunto, estado, prioridad, creado_en, actualizado_en
        FROM tickets
        WHERE usuario_id = %s
        ORDER BY COALESCE(actualizado_en, creado_en) DESC
    ''', (current_user.id,))
    tickets = cursor.fetchall()
    cursor.close()
    return render_template('support.html', tickets = tickets)

@support_bp.route('/crear', methods=['POST'])
@login_required
def create_ticket():
    asunto = request.form.get('subject', '').strip()
    mensaje = request.form.get('message', '').strip()
    if not asunto or not mensaje:
        flash('Completa asunto y mensaje.', 'error')
        return redirect(url_for('support.support_home'))

    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            INSERT INTO tickets (usuario_id, asunto, estado, prioridad, creado_en)
            VALUES (%s, %s, 'abierto', 'media', NOW())
        ''', (current_user.id, asunto))

        ticket_id = cur.lastrowid

        cur.execute('''
            INSERT INTO ticket_mensajes (ticket_id, autor_usuario_id, mensaje, creado_en)
            VALUES (%s, %s, %s, NOW())
        ''', (ticket_id, current_user.id, mensaje))

        mysql.connection.commit()
    except Exception as e:
        mysql.connection.rollback()
        flash('No se pudo crear el ticket. Intenta de nuevo.', 'error')
        raise
    finally:
        cur.close()

    flash('Ticket creado.', 'success')
    return redirect(url_for('support.view_ticket', ticket_id=ticket_id))

@support_bp.route('/t/<int:ticket_id>', methods = ['GET'])
@login_required
def view_ticket(ticket_id):
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT id, usuario_id, asunto, estado FROM tickets WHERE id = %s', (ticket_id,))
    t = cursor.fetchone()
    if not t or t['usuario_id'] != current_user.id:
        cursor.close()
        abort(404)

    cursor.execute('''SELECT id, autor_usuario_id, autor_admin_id, mensaje, creado_en
                   FROM ticket_mensajes
                   WHERE ticket_id = %s ORDER BY creado_en ASC''', (ticket_id,))
    mensajes = cursor.fetchall()
    cursor.close()
    return render_template('ticket_detail.html', ticket = t, mensajes = mensajes)

@support_bp.route('/t/<int:ticket_id>/responder', methods = ['POST'])
@login_required
def reply_ticket(ticket_id):
    texto = request.form.get('message', '').strip()
    if not texto:
        flash('Escribe un mensaje.', 'error')
        return redirect(url_for('support.view_ticket', ticket_id=ticket_id))

    cursor = mysql.connection.cursor()
    cursor.execute('SELECT usuario_id FROM tickets WHERE id = %s', (ticket_id,))
    row = cursor.fetchone()
    if not row or row['usuario_id'] != current_user.id:
        cursor.close()
        abort(404)

    cursor.execute('''INSERT INTO ticket_mensajes (ticket_id, autor_usuario_id, mensaje, creado_en)
                   VALUES (%s, %s, %s, NOW())''', (ticket_id, current_user.id, texto))
    cursor.execute('UPDATE tickets SET estado=\'pendiente\', actualizado_en = NOW() WHERE id = %s', (ticket_id,))
    mysql.connection.commit()
    cursor.close()

    flash('Mensaje enviado.', 'success')
    return redirect(url_for('support.view_ticket', ticket_id=ticket_id))