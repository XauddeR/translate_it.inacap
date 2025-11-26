from flask_mysqldb import MySQL
from flask_login import LoginManager
from flask_mail import Mail

mysql = MySQL()
mail = Mail()
login_manager = LoginManager()