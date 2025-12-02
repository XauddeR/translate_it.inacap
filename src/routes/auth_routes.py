from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from utils.tokens import confirm_reset_token
from services.email_service import send_password_reset_email
from utils.extensions import mysql, limiter
from utils.valid_email import is_valid_email
from werkzeug.security import check_password_hash, generate_password_hash
from models.user_model import create_user, User

auth_bp = Blueprint("auth", __name__, template_folder = "../templates")

@auth_bp.route("/login", methods = ["GET", "POST"])
@limiter.limit("5 per minute", methods = ["POST"])
def login():
    try:
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")

            session["form_data"] = {"email": email}

            if not is_valid_email(email):
                flash("Debes ingresar un correo electrónico válido.", "login_error")
                return redirect(url_for("auth.login"))
            
            if not password or not email:
                flash("Debes ingresar tu correo o contraseña.", "login_error")
                return redirect(url_for("auth.login"))

            cursor = mysql.connection.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            user = cursor.fetchone()
            cursor.close()

            if user and check_password_hash(user["password_bcrypt"], password):
                login_user(User.from_db(user))
                return redirect(url_for("main.index"))
            else:
                flash("Credenciales incorrectas.", "login_error")

        form_data = session.pop("form_data", {})
        return render_template("login.html", form_data = form_data)
    except Exception as e:
        flash("Ocurrió un error inesperado", 'login_error')
        return redirect(url_for("auth.login"))

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))

@auth_bp.route("/register", methods = ["GET", "POST"])
@limiter.limit("3 per minute", methods = ["POST"])
def register():
    try:
        if request.method == "POST":
            username = request.form["usuario"]
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm = request.form["confirm"]

            session["form_data"] = {"usuario": username, "email": email}

            if not is_valid_email(email):
                flash("Debes ingresar un correo electrónico válido.", "register_error")
                return redirect(url_for("auth.register"))

            if password != confirm:
                flash("Las contraseñas no coinciden.", "register_error")
                return redirect(url_for("auth.register"))
            
            if len(password) < 8:
                flash("La contraseña debe tener al menos 8 caracteres.", "register_error")
                return redirect(url_for("auth.register"))
            
            result = create_user(username, email, password)

            if result == "ok":
                flash("Cuenta creada exitosamente.", "login_success")
                return redirect(url_for("auth.login"))
            elif result == "duplicate":
                flash("El correo ingresado ya está registrado", "register_error")
                return redirect(url_for("auth.register"))
            else:
                flash("Ocurrió un error inesperado. Intenta más tarde.", "register_error")
                return redirect(url_for("auth.register"))

        form_data = session.pop("form_data", {})
        return render_template("register.html", form_data = form_data)
    except Exception as e:
        flash("Ocurrió un error inesperado.", "register_error")
        return redirect(url_for("auth.register"))

@auth_bp.route("/forgot-password", methods = ["GET", "POST"])
@limiter.limit("3 per minute", methods = ["POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        if not is_valid_email(email):
            flash("Debes ingresar un correo electrónico válido.", "forgot_error")
            return redirect(request.url)

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = %s LIMIT 1", (email,),)
        user = cursor.fetchone()
        cursor.close()

        if user:
            try:
                send_password_reset_email(user)
            except Exception as e:
                print(f"Error en envio de email: {e}")
                flash("No pudimos enviar el correo en este momento. Intenta de nuevo más tarde.", "forgot_error")
                return redirect(request.url)

        flash("Recibirás un enlace para restablecer tu contraseña en unos momentos.", "forgot_success")

    return render_template("forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods = ["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    email = confirm_reset_token(token, max_age = 3600)
    if not email:
        flash("El enlace de recuperación no es válido o ha expirado.", "reset_error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password")
        confirm = request.form.get("confirm")

        if not password or not confirm:
            flash("Debes ingresar y confirmar la nueva contraseña.", "reset_error")
            return redirect(request.url)

        if password != confirm:
            flash("Las contraseñas no coinciden.", "reset_error")
            return redirect(request.url)

        if len(password) < 8:
            flash("La contraseña debe tener al menos 8 caracteres.", "reset_error")
            return redirect(request.url)

        password_hash = generate_password_hash(password)

        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE usuarios
            SET password_bcrypt = %s
            WHERE email = %s
        """, (password_hash, email),)
        mysql.connection.commit()
        cursor.close()

        flash("Tu contraseña ha sido restablecida correctamente.", "reset_success")
        return redirect(url_for("auth.login"))
    
    return render_template("reset_password.html", token = token)