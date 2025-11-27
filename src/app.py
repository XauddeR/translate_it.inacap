import os
from config import Config
from flask import Flask, render_template, redirect, url_for, flash, current_app
from flask_wtf.csrf import CSRFProtect, CSRFError 
from models.user_model import User
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.upload_routes import upload_bp
from routes.admin_routes import admin_bp
from routes.support_routes import support_bp
from utils.extensions import mysql, login_manager, mail, socketio
from werkzeug.exceptions import RequestEntityTooLarge
from utils.date_filter import format_date

csrf = CSRFProtect()

def translateit():
    app = Flask(__name__)
    app.config.from_object(Config)

    login_manager.login_view = 'auth.login'

    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads', 'videos')
    app.config['THUMBNAIL_FOLDER'] = os.path.join(app.root_path, 'uploads', 'thumbnail')
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok = True)
    os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok = True)
    
    csrf.init_app(app)  
    mysql.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins = '*')

    with app.app_context():
        import utils.socket_events

    app.jinja_env.filters['format_date'] = format_date

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp, url_prefix = '/upload')
    app.register_blueprint(admin_bp, url_prefix = '/admin')
    app.register_blueprint(support_bp, url_prefix = '/support')

    @login_manager.user_loader
    def load_user(user_id):
        cur = mysql.connection.cursor()
        cur.execute('''
            SELECT 
                u.ID AS id,
                u.USUARIO AS usuario,
                u.EMAIL AS email,
                (a.usuario_id IS NOT NULL) AS is_admin
            FROM usuarios u
            LEFT JOIN administradores a ON a.usuario_id = u.ID
            WHERE u.ID = %s
            LIMIT 1
        ''', (user_id,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return None
        user = User.from_db(row)
        if 'is_admin' in row:
            user._is_admin = bool(row['is_admin'])
        return user

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html', error = error), 404
    
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('Sesión expirada o token inválido. Vuelve a intentar.', 'error')
        return redirect(url_for('main.index')), 400
    
    @app.errorhandler(RequestEntityTooLarge)
    def handle_file_too_large(e):
        flash('El archivo supera el tamaño máximo permitido (200 MB).', 'upload_error')
        return redirect(url_for('upload.upload_file'))
    
    return app

if __name__ == '__main__':
    app = translateit()
    socketio.run(app, host = '0.0.0.0', port = 5000, debug = True)