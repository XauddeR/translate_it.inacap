from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import check_password_hash
from models.user_model import create_user, User
from utils.extensions import mysql

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

        if create_user(usuario, email, password):
            return redirect(url_for('auth.login'))
        else:
            flash('Hubo un error al registrar usuario', 'register_error')
            return redirect(url_for('auth.register'))

    return render_template('register.html')