from utils.extensions import mysql
from werkzeug.security import generate_password_hash
from MySQLdb.cursors import DictCursor
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
            cursor = mysql.connection.cursor(DictCursor)
            cursor.execute('SELECT 1 FROM ADMINISTRADORES WHERE USUARIO_ID = %s', (self.id,))
            result = cursor.fetchone()
            cursor.close()
            self._is_admin = bool(result)
        return self._is_admin

    @staticmethod
    def from_db(row):
        return User(
            id = row['id'],
            usuario = row['usuario'],
            email = row['email'],
        )

def create_user(usuario, email, password):
    try:
        cursor = mysql.connection.cursor()
        hashed_password = generate_password_hash(password)
        sql = '''
            INSERT INTO USUARIOS (USUARIO, EMAIL, PASSWORD_BCRYPT)
            VALUES (%s, %s, %s)
        '''
        cursor.execute(sql, (usuario, email, hashed_password))
        mysql.connection.commit()
        cursor.close()
        return True
    
    except Exception as e:
        print('Error al crear usuario:', e)
        return False