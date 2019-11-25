import psycopg2
from psycopg2 import sql

conn = psycopg2.connect(dbname='rabota', user='postgres', password='root', host='localhost')
cur = conn.cursor()

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

def areasLoad():
    cur.execute("select * from area")
    result = cur.fetchall()
    result_new = list(sum(result, ()))
    conn.commit()
    return result_new