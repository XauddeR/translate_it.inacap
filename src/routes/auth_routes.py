from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from utils.tokens import confirm_reset_token
from services.email_service import send_password_reset_email
from utils.extensions import mysql
from flask_mail import Message
from werkzeug.security import check_password_hash, generate_password_hash
from models.user_model import create_user, User

auth_bp = Blueprint('auth', __name__, template_folder = '../templates')

@auth_bp.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE email = %s', (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password_bcrypt'], password):
            login_user(User.from_db(user))
            return redirect(url_for('main.index'))
        else:
            flash('Credenciales incorrectas', 'login_error')
            
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario = request.form['usuario']
        email = request.form['email']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            flash('Las contraseñas no coinciden', 'register_error')
            return redirect(request.url)

        if create_user(usuario, email, password):
            return redirect(url_for('auth.login'))
        else:
            flash('Hubo un error al registrar usuario', 'register_error')
            return redirect(url_for('auth.register'))

    return render_template('register.html')

@auth_bp.route('/forgot-password', methods = ['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Debes ingresar un correo electrónico.', 'forgot_error')
            return redirect(request.url)

        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT * FROM usuarios WHERE email = %s LIMIT 1',
            (email,),
        )
        user = cursor.fetchone()
        cursor.close()

        if user:
            try:
                send_password_reset_email(user)
            except Exception as e:
                print('Error en envio de email: ', e)
                flash('No pudimos enviar el correo en este momento. Intenta de nuevo más tarde.', 'forgot_error')
                return redirect(request.url)

        flash('Recibirás un enlace para restablecer tu contraseña en unos momentos.', 'forgot_success')

    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods = ['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    email = confirm_reset_token(token, max_age = 3600)
    if not email:
        flash('El enlace de recuperación no es válido o ha expirado.', 'reset_error')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if not password or not confirm:
            flash('Debes ingresar y confirmar la nueva contraseña.', 'reset_error')
            return redirect(request.url)

        if password != confirm:
            flash('Las contraseñas no coinciden.', 'reset_error')
            return redirect(request.url)

        if len(password) < 8:
            flash('La contraseña debe tener al menos 8 caracteres.', 'reset_error')
            return redirect(request.url)

        password_hash = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        cursor.execute(
            '''
            UPDATE usuarios
            SET password_bcrypt = %s
            WHERE email = %s
            ''',
            (password_hash, email),
        )
        mysql.connection.commit()
        cursor.close()

        flash('Tu contraseña ha sido restablecida correctamente.', 'reset_success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token = token)