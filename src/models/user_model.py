from utils.extensions import mysql
from werkzeug.security import generate_password_hash
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, usuario, email, rol):
        self.id = id
        self.usuario = usuario
        self.email = email
        self.rol = rol

    @staticmethod
    def from_db(row):
        return User(
            id = row['id'],
            usuario = row['usuario'],
            email = row['email'],
            rol = row['rol']
        )

def create_user(usuario, email, password, rol = 'usuario'):
    try:
        cursor = mysql.connection.cursor()
        hashed_password = generate_password_hash(password)
        sql = '''
            INSERT INTO usuarios (usuario, email, password_bcrypt, rol)
            VALUES (%s, %s, %s, %s)
        '''
        cursor.execute(sql, (usuario, email, hashed_password, rol))
        mysql.connection.commit()
        cursor.close()
        return True
    
    except Exception as e:
        print('Error al crear usuario:', e)
        return False