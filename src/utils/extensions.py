from flask_mysqldb import MySQL
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

mysql = MySQL()
socketio = SocketIO(
    cors_allowed_origins = "*",
    async_mode = "threading"
)
mail = Mail()
login_manager = LoginManager()
limiter = Limiter(
    key_func = get_remote_address,
    default_limits = []
)