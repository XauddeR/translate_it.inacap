from utils.extensions import mysql

def get_lang(active_only = False):
    cursor = mysql.connection.cursor()
    query = 'SELECT * FROM idiomas'
    if active_only:
        query += ' WHERE habilitado = 1'
    query += ' ORDER BY nombre'
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    return rows

def add_lang(nombre, codigo):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('INSERT INTO idiomas (nombre, codigo, habilitado) VALUES (%s, %s, 1)', (nombre, codigo))
        mysql.connection.commit()
        cursor.close()
    except Exception as e:
        print(f'Error al intentar añadir nuevo idioma: {e}')

def disable_lang(idioma_id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('UPDATE idiomas SET habilitado = 0 WHERE id = %s', (idioma_id,))
        mysql.connection.commit()
        cursor.close()
    except Exception as e:
        print(f'Error al intentar deshabilitar idioma: {e}')


def enable_lang(idioma_id):
    cursor = mysql.connection.cursor()
    try:
        cursor.execute('UPDATE idiomas SET habilitado = 1 WHERE id = %s', (idioma_id,))
        mysql.connection.commit()
        cursor.close()
    except Exception as e:
        print(f'Error al intentar habilitar idioma: {e}')