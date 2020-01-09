import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash, check_password_hash
from transliterate import translit, get_available_language_codes

conn = psycopg2.connect(dbname='rabota', user='postgres', password='root', host='localhost')
cur = conn.cursor()

def createAdmin():
    adminPswdHash = generate_password_hash('admin')

    try:
        cur.execute("insert into person (login, password, status, email, phone) values ('admin', %s, 'admin', 'admin@admin.ru', '0000000000')", (adminPswdHash, ))
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        pass

def loadInfoFromProfile(columnname, tablename, name):
    cur.execute(
        sql.SQL("SELECT {0} FROM {1} WHERE user_id = (select user_id from person where login = %s)")
            .format(sql.Identifier(columnname), sql.Identifier(tablename)),[name])
    result = cur.fetchone()
    profileData = ''
    if result is not None:
        profileData = result[0]
    conn.commit()
    return profileData

def loadInfoFromPerson(columnname, name):
    cur.execute(
        sql.SQL("SELECT {} FROM person WHERE user_id = (select user_id from person where login = %s)")
            .format(sql.Identifier(columnname)), [name])
    result = cur.fetchone()
    profileData = ''
    if result is not None:
        profileData = result[0]
    conn.commit()
    return profileData

def userExist(tablename, id):
    cur.execute(sql.SQL("SELECT user_id FROM {} WHERE user_id = %s").format(sql.Identifier(tablename)), [id])
    result = cur.fetchone()
    if result is not None:
        item = 1
    else:
        item = 0
    conn.commit()
    return item

def selectColumn(columnname, tablename):
    cur.execute(sql.SQL("SELECT {0} FROM {1}").format(sql.Identifier(columnname), sql.Identifier(tablename)))
    result = cur.fetchall()
    result_new = list(sum(result, ()))
    conn.commit()
    return result_new

def getUserID(name):
    cur.execute('SELECT user_id FROM person WHERE login = %s', (name,))
    result = cur.fetchone()
    ID = ''
    if result is not None:
        ID = result[0]
    conn.commit()
    return ID

def translitToURL(data):
    dataUni = translit(data, 'ru', reversed=True)
    dataURL = "_".join(dataUni.split())
    dataURLLow = dataURL.lower()
    return dataURLLow

def translitFromURL(data):
    dataURL = translit(data, 'ru')
    dataURL = dataURL.capitalize()
    dataRus = dataURL.replace('~', ' ')
    return dataRus
