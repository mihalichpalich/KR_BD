import psycopg2
from psycopg2 import sql

conn = psycopg2.connect(dbname='rabota', user='postgres', password='root', host='localhost')
cur = conn.cursor()

def createDatabase():
    try:
        cur.execute(
            "CREATE TABLE if not exists person (user_id serial primary key, login varchar(15) NOT null unique, password TEXT NOT NULL, status TEXT NOT NULL, email TEXT NOT NULL unique, phone TEXT NOT NULL unique);")
        conn.commit()
        cur.execute(
            "CREATE TABLE if not exists company (user_id int primary key references person, inn varchar(10) NOT null unique, company_name TEXT NOT NULL);")
        conn.commit()
        cur.execute(
            "CREATE TABLE if not exists employee (user_id int primary key references person, full_name text NOT null);")
        conn.commit()
        cur.execute(
            "CREATE TABLE if not exists customer (user_id int primary key references person, customer_name text NOT null);")
        conn.commit()
        cur.execute("CREATE TABLE if not exists area (area_name text not null primary key);")
        conn.commit()
        cur.execute(
            "CREATE TABLE if not exists performer (user_id int primary key references person, performer_name text NOT null, area_name text NOT null references area, services_descr TEXT NOT NULL);")
        conn.commit()
        cur.execute("CREATE TABLE if not exists industry (industry_name text not null primary key);")
        conn.commit()
        cur.execute("CREATE TABLE if not exists profession (profession_name text not null primary key);")
        conn.commit()
        cur.execute("CREATE TABLE if not exists industry_profession (industry_name text not null, profession_name text not null, foreign key (industry_name) references industry on update cascade, foreign key (profession_name) references profession on update cascade);")
        conn.commit()
        cur.execute("CREATE TABLE if not exists vacancy (vacancy_id serial primary key, user_id int references person, industry_name text not null references industry on update cascade, profession_name text not null references profession on update cascade, employee_sex text, min_emp_age int not null, max_emp_age int, min_salary int not null, min_exp int not null, emp_type text not null, vac_pub_data text not null);")
        conn.commit()
        cur.execute(
            "CREATE TABLE if not exists cv (cv_id serial primary key, user_id int references person, industry_name text not null references industry on update cascade, profession_name text not null references profession on update cascade, min_salary int, max_salary int, exp int not null, emp_type text not null, cv_pub_data text not null);")
        conn.commit()
        cur.execute(
            "CREATE TABLE if not exists browsing (user_id int not null, cv_id int not null, view_data text not null, foreign key (user_id) references company, foreign key (cv_id) references cv);")
        conn.commit()
        cur.execute(
            "CREATE TABLE if not exists task (task_id serial primary key, user_id int references person, area_name text not null references area on update cascade, task_descr text not null, exec_date text not null, price int not null);")
        conn.commit()
    except Exception as e:
        print(e)

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