from flask_mysqldb import MySQL
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO

mysql = MySQL()
socketio = SocketIO(
    cors_allowed_origins="*",
    async_mode="threading"
)
mail = Mail()
login_manager = LoginManager()