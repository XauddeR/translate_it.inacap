from utils.extensions import mysql

def get_lang(active_only = False):
    cur = mysql.connection.cursor()
    query = 'SELECT * FROM idiomas'
    if active_only:
        query += ' WHERE habilitado = 1'
    query += ' ORDER BY nombre'
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    return rows

def add_lang(nombre, codigo):
    cur = mysql.connection.cursor()
    cur.execute(
        'INSERT INTO idiomas (nombre, codigo, habilitado) VALUES (%s, %s, 1)',
        (nombre, codigo)
    )
    mysql.connection.commit()
    cur.close()

def disable_lang(idioma_id):
    cur = mysql.connection.cursor()
    cur.execute('UPDATE idiomas SET habilitado = 0 WHERE id = %s', (idioma_id,))
    mysql.connection.commit()
    cur.close()

def enable_lang(idioma_id):
    cur = mysql.connection.cursor()
    cur.execute('UPDATE idiomas SET habilitado = 1 WHERE id = %s', (idioma_id,))
    mysql.connection.commit()
    cur.close()

def delete_lang(idioma_id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM idiomas WHERE id = %s', (idioma_id,))
    mysql.connection.commit()
    cur.close()