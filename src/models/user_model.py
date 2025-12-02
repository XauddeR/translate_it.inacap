from flask_mysqldb import MySQLdb
from MySQLdb import IntegrityError
from utils.extensions import mysql
from werkzeug.security import generate_password_hash
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, usuario, email):
        self.id = id
        self.usuario = usuario
        self.email = email
        self._is_admin = None

    @property
    def is_admin(self):
        if self._is_admin is None:
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT 1 FROM administradores WHERE usuario_id = %s LIMIT 1", (self.id,))
            self._is_admin = cursor.fetchone() is not None
            cursor.close()
        return self._is_admin

    @staticmethod
    def from_db(row):
        return User(
            id = row["id"],
            usuario = row["usuario"],
            email = row["email"],
        )

def create_user(usuario, email, password):
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        hashed_password = generate_password_hash(password)
        sql = """
            INSERT INTO usuarios (usuario, email, password_bcrypt)
            VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (usuario, email, hashed_password))
        mysql.connection.commit()
        return "ok"
    
    except IntegrityError as e:
        print(f"Email duplicado: {e}")
        mysql.connection.rollback()
        return "duplicate"
    
    except Exception as e:
        print(f"Error al crear usuario: {e}")
        mysql.connection.rollback()
        return "error"
    
    finally:
        if cursor is not None:
            cursor.close()