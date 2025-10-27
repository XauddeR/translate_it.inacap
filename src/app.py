import os
from config import Config
from flask import Flask, render_template
from models.user_model import User
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.upload_routes import upload_bp
from routes.admin_routes import admin_bp
from utils.extensions import mysql, login_manager

def translateit():
    app = Flask(__name__)
    app.config.from_object(Config)

    mysql.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'

    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads', 'videos')
    app.config['THUMBNAIL_FOLDER'] = os.path.join(app.root_path, 'uploads', 'thumbnail')
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok = True)
    os.makedirs(app.config['THUMBNAIL_FOLDER'], exist_ok = True)

    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp, url_prefix = '/upload')
    app.register_blueprint(admin_bp, url_prefix = '/admin')
    app.register_blueprint(auth_bp)

    @login_manager.user_loader
    def load_user(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM USUARIOS WHERE ID = %s', (user_id,))
        row = cursor.fetchone()
        cursor.close()
        if row:
            return User.from_db({
                'id': row[0],
                'usuario': row[1],
                'email': row[2]
            })
        return None

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('404.html', error = error), 404

    return app

if __name__ == '__main__':
    app = translateit()
    app.run(debug = True)