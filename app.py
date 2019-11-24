from flask import *
from flask_bootstrap import Bootstrap
import psycopg2
from psycopg2 import sql

app = Flask(__name__)
Bootstrap(app)

conn = psycopg2.connect(dbname='rabota', user='postgres', password='root', host='localhost')
cur = conn.cursor()

try:
    cur.execute("CREATE TABLE if not exists person (user_id serial primary key, login varchar(15) NOT null unique, password TEXT NOT NULL, status TEXT NOT NULL, email TEXT NOT NULL unique, phone TEXT NOT NULL unique);")
    conn.commit()
    cur.execute("CREATE TABLE if not exists company (user_id int primary key references person, inn varchar(10) NOT null unique, company_name TEXT NOT NULL);")
    conn.commit()
    cur.execute("CREATE TABLE if not exists employee (user_id int primary key references person, full_name text NOT null);")
    conn.commit()
    cur.execute("CREATE TABLE if not exists customer (user_id int primary key references person, customer_name text NOT null);")
    conn.commit()
    cur.execute("CREATE TABLE if not exists area (area_name text not null primary key);")
    conn.commit()
    cur.execute("CREATE TABLE if not exists performer (user_id int primary key references person, perfomer_name text NOT null, area_name text NOT null references area, services_descr TEXT NOT NULL);")
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

@app.route('/')
def index():
    return render_template("index.html")

# регистрация
@app.route('/sign_up', methods=['GET', 'POST'])
def signUp():
    if request.method == 'POST':
        login = request.form.get('username')
        password = request.form.get('password')
        status = request.form.get('status')
        email = request.form.get('email')
        phone = request.form.get('phone')

        if login == '' or password == '' or email == '' or phone == '':
            return render_template("sign_up.html", message='Пожайлуста, заполните все поля')
        elif status == '':
            return render_template("sign_up.html", message='Пожайлуста, выберите свой статус')

        try:
            cur.execute("insert into person (login, password, status, email, phone) values (%s, %s, %s, %s, %s)", (login, password, status, email, phone))
            conn.commit()
            return redirect(url_for('success'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return render_template("sign_up.html", message='Пользователь с данным логином, email или телефоном уже существует!')
        except psycopg2.errors.StringDataRightTruncation:
            conn.rollback()
            return render_template("sign_up.html", message='Логин должен состоять не более чем из 15 символов!')
    return render_template("sign_up.html")

# успешная регистрация
# убрать метод get когда все будет готово
@app.route('/success', methods=['GET', 'POST'])
def success():
    return render_template("success.html")

# вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == '' or password == '':
            return render_template("login.html", message='Пожайлуста, заполните все поля!')

        if username == 'admin' and password == 'admin':
            return redirect(url_for('admin'))

        cur.execute('SELECT * FROM person WHERE login = %s and password = %s', (username, password, ))
        if cur.rowcount == 0:
            return render_template("login.html", message='Пользователя с данным логином не существует или указан неверный пароль!')
        conn.commit()

        cur.execute('SELECT status FROM person WHERE login = %s and password = %s', (username, password, ))
        result = cur.fetchone()
        status = result[0]
        conn.commit()
        return redirect(url_for('profile', status=status, username=username))
    return render_template("login.html")

# восстановление пароля
@app.route('/pw_rec')
def pwRec():
    return render_template("pw_rec.html")

# успешное восстановление пароля
@app.route('/pw_rec_suc', methods=['GET', 'POST'])
def pwRecSuc():
    if request.method == 'POST':
        login = request.form.get('username')

        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        cur.execute('SELECT * FROM person WHERE login = %s', (login, ))
        if cur.rowcount == 0:
            return render_template("pw_rec.html", message='Пользователя с данным логином не существует!')
        conn.commit()

        if password1 != password2:
            return render_template("pw_rec.html", message='Пароли не совпадают!')

        cur.execute('update person set password = %s WHERE login = %s', (password2, login, ))
        conn.commit()
    return render_template("pw_rec_suc.html")

# страница профиля
@app.route('/profile/<status>/<username>', methods=['GET', 'POST'])
def profile(status, username):
    if status == 'company':
        # загружаем инн
        inn = loadInfoFromProfile('inn', 'company', username)
        # загружаем название
        companyName = loadInfoFromProfile('company_name', 'company', username)
        # загружаем телефон
        companyPhone = loadInfoFromPerson('phone', username)
        # загружаем email
        companyEmail = loadInfoFromPerson('email', username)
        return render_template("profile.html", status=status, username=username, inn=inn, companyName=companyName, companyPhone=companyPhone, companyEmail=companyEmail)

    if status == 'employee':
        # загружаем фио
        fullName = loadInfoFromProfile('full_name', 'employee', username)
        # загружаем телефон
        employeePhone = loadInfoFromPerson('phone', username)
        # загружаем email
        employeeEmail = loadInfoFromPerson('email', username)
        return render_template("profile.html", status=status, username=username, fullName=fullName,
                               employeePhone=employeePhone, employeeEmail=employeeEmail)

    if status == 'customer':
        # загружаем имя
        customerName = loadInfoFromProfile('customer_name', 'customer', username)
        # загружаем телефон
        customerPhone = loadInfoFromPerson('phone', username)
        # загружаем email
        customerEmail = loadInfoFromPerson('email', username)
        return render_template("profile.html", status=status, username=username, customerName=customerName, customerPhone=customerPhone, customerEmail=customerEmail)
    #
    # if status == 'performer':
    #     # загружаем имя
    #     cur.execute(  #         'SELECT customer_name FROM customer WHERE user_id = (select user_id from person where login = %s)',
    #         (username,))
    #     result = cur.fetchone()
    #     customerName = ''
    #     if result is not None:
    #         customerName = result[0]
    #     conn.commit()
    #
    #     # загружаем телефон
    #     cur.execute(
    #         'SELECT customer_phone FROM customer WHERE user_id = (select user_id from person where login = %s)',
    #         (username,))
    #     result = cur.fetchone()
    #     customerPhone = ''
    #     if result is not None:
    #         customerPhone = result[0]
    #     conn.commit()
    #
    #     # загружаем email
    #     cur.execute(
    #         'SELECT customer_email FROM customer WHERE user_id = (select user_id from person where login = %s)',
    #         (username,))
    #     result = cur.fetchone()
    #     customerEmail = ''
    #     if result is not None:
    #         customerEmail = result[0]
    #     conn.commit()
    #     return render_template("profile.html", status=status, username=username, customerName=customerName,
    #                            customerPhone=customerPhone, customerEmail=customerEmail)

# страница редактирования профиля
@app.route('/profile_edit/<status>/<username>', methods=['GET', 'POST'])
def profileEdit(status, username):
    cur.execute('SELECT user_id FROM person WHERE login = %s', (username, ))
    result = cur.fetchone()
    userID = ''
    if result is not None:
        userID = result[0]
    conn.commit()

    if status == 'company':
        if request.method == 'POST':
            inn = request.form.get('inn')
            companyName = request.form.get('company_name')
            companyPhone = request.form.get('company_phone')
            companyEmail = request.form.get('company_email')

            isCompany = userExist('company', userID)

            try:
                if isCompany == 0:
                    if inn == '' or companyName == '' or companyPhone == '' or companyEmail == '':
                        return render_template("profile_edit.html", message='Пожайлуста, заполните все поля')
                    cur.execute("insert into company (user_id, inn, company_name) values (%s, %s, %s)", (userID, inn, companyName, ))
                else:
                    if inn != '':
                        cur.execute('update company set inn = %s WHERE user_id = %s', (inn, userID, ))
                    if companyName != '':
                        cur.execute('update company set company_name = %s WHERE user_id = %s', (companyName, userID,))
                    if companyPhone != '':
                        cur.execute('update person set phone = %s WHERE user_id = %s', (companyPhone, userID,))
                    if companyEmail != '':
                        cur.execute('update person set email = %s WHERE user_id = %s', (companyEmail, userID,))
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("profile_edit.html", message='Пользователь с данным ИНН или телефоном уже существует!')
            except psycopg2.errors.StringDataRightTruncation:
                conn.rollback()
                return render_template("profile_edit.html", message='ИНН должен состоять не более чем из 10 символов!')
            return redirect(url_for('profile', status=status, username=username))

    if status == 'employee':
        if request.method == 'POST':
            fullName = request.form.get('full_name')
            employeePhone = request.form.get('employee_phone')
            employeeEmail = request.form.get('employee_email')

            isEmployee = userExist('employee', userID)

            try:
                if isEmployee == 0:
                    if fullName == '' or employeePhone == '' or employeeEmail == '':
                        return render_template("profile_edit.html", message='Пожайлуста, заполните все поля')
                    cur.execute("insert into employee (user_id, full_name) values (%s, %s)", (userID, fullName, ))
                else:
                    if fullName != '':
                        cur.execute('update employee set full_name = %s WHERE user_id = %s', (fullName, userID, ))
                    if employeePhone != '':
                        cur.execute('update person set phone = %s WHERE user_id = %s', (employeePhone, userID,))
                    if employeeEmail != '':
                        cur.execute('update person set email = %s WHERE user_id = %s', (employeeEmail, userID,))
                    conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("profile_edit.html", message='Пользователь с данным телефоном уже существует!')
            return redirect(url_for('profile', status=status, username=username))

    if status == 'customer':
        if request.method == 'POST':
            customerName = request.form.get('customer_name')
            customerPhone = request.form.get('customer_phone')
            customerEmail = request.form.get('customer_email')

            isCustomer = userExist('employee', userID)

            try:
                if isCustomer == 0:
                    if customerName == '' or customerPhone == '' or customerEmail == '':
                        return render_template("profile_edit.html", message='Пожайлуста, заполните все поля')
                    cur.execute("insert into customer (user_id, customer_name) values (%s, %s)", (userID, customerName, ))
                else:
                    if customerName != '':
                        cur.execute('update customer set customer_name = %s WHERE user_id = %s', (customerName, userID, ))
                    if customerPhone != '':
                        cur.execute('update person set phone = %s WHERE user_id = %s', (customerPhone, userID,))
                    if customerEmail != '':
                        cur.execute('update person set email = %s WHERE user_id = %s', (customerEmail, userID,))
                    conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("profile_edit.html", message='Пользователь с данным телефоном уже существует!')
            return redirect(url_for('profile', status=status, username=username))

    return render_template("profile_edit.html", status=status, username=username)

# панель администратора
@app.route('/admin')
def admin():
    return render_template("admin.html")

# админка, работа с данными
@app.route('/admin_data')
def adminData():
    return render_template("admin_data.html")

# админка, отрасли и должности
@app.route('/admin_data_ip')
def adminDataIP():
    return render_template("admin_data_ip.html")

# АДМИНКА, СФЕРЫ ДЕЯТЕЛЬНОСТИ
@app.route('/admin_data_areas')
def adminDataAreas():
    return render_template("admin_data_areas.html")

# добавление
@app.route('/admin_data_areas_add', methods=['GET', 'POST'])
def adminDataAreasAdd():
    cur.execute("select * from area")
    result = cur.fetchall()
    result_new = list(sum(result, ()))
    conn.commit()

    if request.method == 'POST':
        area = request.form.get('area')

        if area != '':
            try:
                cur.execute("insert into area (area_name) values (%s)", (area, ))
                conn.commit()
                return redirect(url_for('adminDataAreasAdd', areas=result_new))
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("admin_data_areas_add.html", message='Данная сфера деятельности уже существует!')
    return render_template("admin_data_areas_add.html", areas=result_new)

# изменение
@app.route('/admin_data_areas_edit', methods=['GET', 'POST'])
def adminDataAreasEdit():
    cur.execute("select * from area")
    result = cur.fetchall()
    result_new = list(sum(result, ()))
    conn.commit()

    if request.method == 'POST':
        areaOld = request.form.get('old_area')
        areaNew = request.form.get('new_area')

        if areaOld == '' or areaNew == '':
            return render_template("admin_data_areas_add.html", message='Введите название!')
        else:
            try:
                cur.execute("update area set area_name = %s WHERE area_name = %s", (areaNew, areaOld))
                conn.commit()
                return redirect(url_for('adminDataAreasEdit'))
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("admin_data_areas_edit.html", message='Данная сфера деятельности уже существует!')
    return render_template("admin_data_areas_edit.html", areas=result_new)

@app.route('/vacancy_cat')
def vacancyCat():
    vacancies = ["Engineer", "Programmist", "Cleaner"]
    return render_template("vacancy_cat.html", vacancies=vacancies)

@app.route('/cv_cat')
@app.route('/cv_cat/<username>')
def CVCat(username=None):
    return render_template("cv_cat.html", user=username)

if __name__ == '__main__':
    app.run(debug=True)
