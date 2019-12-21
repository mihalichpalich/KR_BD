import os

from flask import *
from flask_bootstrap import Bootstrap
from werkzeug.security import generate_password_hash, check_password_hash

from functions import *

app = Flask(__name__)
app.secret_key = os.urandom(24)
Bootstrap(app)

createDatabase()

@app.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = session['user']

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

        passwordHash = generate_password_hash(password)

        try:
            cur.execute("insert into person (login, password, status, email, phone) values (%s, %s, %s, %s, %s)", (login, passwordHash, status, email, phone))
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
        session.pop('user', None)

        username = request.form.get('username')
        password = request.form.get('password')

        if username == '' or password == '':
            return render_template("login.html", message='Пожайлуста, заполните все поля!')

        if username == 'admin' and password == 'admin':
            return redirect(url_for('admin'))

        cur.execute('SELECT user_id, password, status FROM person WHERE login = %s', (username, ))
        if cur.rowcount == 0:
            return render_template("login.html", message='Пользователя с данным логином не существует!')
        result = cur.fetchone()
        user_id = result[0]
        passwordHash = result[1]
        status = result[2]
        conn.commit()

        resultHash = check_password_hash(passwordHash, password)
        if not resultHash:
            return render_template("login.html", message='Введен неправильный пароль!')

        session['user'] = user_id
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

        passwordHash = generate_password_hash(password2)

        cur.execute('update person set password = %s WHERE login = %s', (passwordHash, login, ))
        conn.commit()
    return render_template("pw_rec_suc.html")

# страница профиля
@app.route('/profile/<status>/<username>', methods=['GET', 'POST'])
def profile(status, username):
    if g.user:
        warning = ''

        if status == 'company':
            # загружаем инн
            inn = loadInfoFromProfile('inn', 'company', username)
            # загружаем название
            companyName = loadInfoFromProfile('company_name', 'company', username)
            # загружаем телефон
            companyPhone = loadInfoFromPerson('phone', username)
            # загружаем email
            companyEmail = loadInfoFromPerson('email', username)

            if inn == '' or companyName == '':
                warning = True
            return render_template("profile.html", status=status, username=username, inn=inn, companyName=companyName,
                                   companyPhone=companyPhone, companyEmail=companyEmail, warning=warning)

        if status == 'employee':
            # загружаем фио
            fullName = loadInfoFromProfile('full_name', 'employee', username)
            # загружаем телефон
            employeePhone = loadInfoFromPerson('phone', username)
            # загружаем email
            employeeEmail = loadInfoFromPerson('email', username)

            if fullName == '':
                warning = True
            return render_template("profile.html", status=status, username=username, fullName=fullName,
                                   employeePhone=employeePhone, employeeEmail=employeeEmail, warning=warning)

        if status == 'customer':
            # загружаем имя
            customerName = loadInfoFromProfile('customer_name', 'customer', username)
            # загружаем телефон
            customerPhone = loadInfoFromPerson('phone', username)
            # загружаем email
            customerEmail = loadInfoFromPerson('email', username)

            if customerName == '':
                warning = True
            return render_template("profile.html", status=status, username=username, customerName=customerName,
                                   customerPhone=customerPhone, customerEmail=customerEmail, warning=warning)

        if status == 'performer':
            # загружаем имя
            performerName = loadInfoFromProfile('performer_name', 'performer', username)
            # загружаем сферу деятельности
            performerArea = loadInfoFromProfile('area_name', 'performer', username)
            # загружаем описание услуг
            servicesDescr = loadInfoFromProfile('services_descr', 'performer', username)
            # загружаем телефон
            performerPhone = loadInfoFromPerson('phone', username)
            # загружаем email
            performerEmail = loadInfoFromPerson('email', username)


            if performerName == '' or performerArea == '' or servicesDescr == '':
                warning = True
            return render_template("profile.html", status=status, username=username, performerName=performerName,
                                   servicesDescr=servicesDescr, performerArea=performerArea, performerPhone=performerPhone,
                                   performerEmail=performerEmail, warning=warning)
    return render_template("login.html")

# страница редактирования профиля
@app.route('/profile_edit/<status>/<username>', methods=['GET', 'POST'])
def profileEdit(status, username):
    if g.user:
        userID = getUserID(username)

        if status == 'company':
            if request.method == 'POST':
                inn = request.form.get('inn')
                companyName = request.form.get('company_name')
                companyPhone = request.form.get('company_phone')
                companyEmail = request.form.get('company_email')

                isCompany = userExist('company', userID)

                try:
                    if isCompany == 0:
                        if inn == '' or companyName == '':
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
                    return render_template("profile_edit.html", message='Пользователь с данным ИНН, телефоном или email уже существует!', status=status, username=username)
                except psycopg2.errors.StringDataRightTruncation:
                    conn.rollback()
                    return render_template("profile_edit.html", message='ИНН должен состоять не более чем из 10 символов!', status=status, username=username)
                return redirect(url_for('profile', status=status, username=username))

        if status == 'employee':
            if request.method == 'POST':
                fullName = request.form.get('full_name')
                employeePhone = request.form.get('employee_phone')
                employeeEmail = request.form.get('employee_email')

                isEmployee = userExist('employee', userID)

                try:
                    if isEmployee == 0:
                        if fullName == '':
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
                    return render_template("profile_edit.html", message='Пользователь с данным телефоном или email уже существует!', status=status, username=username)
                return redirect(url_for('profile', status=status, username=username))

        if status == 'customer':
            if request.method == 'POST':
                customerName = request.form.get('customer_name')
                customerPhone = request.form.get('customer_phone')
                customerEmail = request.form.get('customer_email')

                isCustomer = userExist('employee', userID)

                try:
                    if isCustomer == 0:
                        if customerName == '':
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
                    return render_template("profile_edit.html", message='Пользователь с данным телефоном или email уже существует!', status=status, username=username)
                return redirect(url_for('profile', status=status, username=username))

        if status == 'performer':
            areas = selectColumn('area_name','area')

            if request.method == 'POST':
                performerName = request.form.get('performer_name')
                performerArea = request.form.get('performer_area')
                servicesDescr = request.form.get('services_descr')
                performerPhone = request.form.get('performer_phone')
                performerEmail = request.form.get('performer_email')

                isPerformer = userExist('performer', userID)

                try:
                    if isPerformer == 0:
                        if performerName == '' or performerArea == '' or servicesDescr == '':
                            return render_template("profile_edit.html", message='Пожайлуста, заполните все поля', status=status, username=username, areas=areas)
                        cur.execute("insert into performer (user_id, performer_name, area_name, services_descr) values (%s, %s, %s, %s)", (userID, performerName, performerArea, servicesDescr, ))
                    else:
                        if performerName != '':
                            cur.execute('update performer set performer_name = %s WHERE user_id = %s', (performerName, userID, ))
                        if performerArea != '':
                            cur.execute('update performer set area_name = %s WHERE user_id = %s', (performerArea, userID, ))
                        if servicesDescr != '':
                            cur.execute('update performer set services_descr = %s WHERE user_id = %s', (servicesDescr, userID, ))
                        if performerPhone != '':
                            cur.execute('update person set phone = %s WHERE user_id = %s', (performerPhone, userID,))
                        if performerEmail != '':
                            cur.execute('update person set email = %s WHERE user_id = %s', (performerEmail, userID,))
                        conn.commit()
                except psycopg2.errors.UniqueViolation:
                    conn.rollback()
                    return render_template("profile_edit.html", message='Пользователь с данным телефоном или email уже существует!', status=status, username=username, areas=areas)
                return redirect(url_for('profile', status=status, username=username))
            return render_template("profile_edit.html", status=status, username=username, areas=areas)
    return render_template("profile_edit.html", status=status, username=username)

# добавление записи
@app.route('/create_item/<status>/<username>', methods=['GET', 'POST'])
def createItem(status, username):
    industries = selectColumn('industry_name', 'industry')
    professions = selectColumn('profession_name', 'profession')

    if g.user:
        userID = getUserID(username)

        if status == 'company':
            if request.method == 'POST':
                industryName = request.form.get('industry_name')
                professionName = request.form.get('profession_name')
                employeeSex = request.form.get('employee_sex')
                minEmpAge = request.form.get('min_emp_age')
                maxEmpAge = request.form.get('max_emp_age')
                minSalary = request.form.get('min_salary')
                minExp = request.form.get('min_exp')
                empType = request.form.get('emp_type')

                cur.execute('SELECT CURRENT_DATE')
                result = cur.fetchone()
                vacPubData = result[0]

                if maxEmpAge == '':
                    maxEmpAge = None

                try:
                    if industryName == '' or professionName == '' or minEmpAge == '' or minSalary == '' or minExp == '' or empType == '':
                        return render_template("create_item.html", message='Пожайлуста, заполните все поля', status=status, username=username, industries=industries, professions=professions)
                    else:
                        cur.execute(
                            "insert into vacancy (user_id, industry_name, profession_name, employee_sex, min_emp_age, max_emp_age, min_salary, min_exp, emp_type, vac_pub_data) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (userID, industryName, professionName, employeeSex, minEmpAge,
                             maxEmpAge, minSalary, minExp, empType, vacPubData))
                        conn.commit()
                except psycopg2.errors.InvalidTextRepresentation:
                    conn.rollback()
                    return render_template("create_item.html", message='В численные поля записан текст!', status=status, username=username, industries=industries, professions=professions)
                return redirect(url_for('itemList', status=status, username=username))
    return render_template("create_item.html", status=status, username=username, industries=industries, professions=professions)

# список записей
@app.route('/item_list/<status>/<username>')
def itemList(status, username):
    if g.user:
        userID = getUserID(username)

        if status == 'company':
            cur.execute('SELECT industry_name, profession_name, employee_sex, min_emp_age, max_emp_age, min_salary, min_exp, emp_type, vac_pub_data FROM vacancy WHERE login = %s', (username,))
    return render_template("item_list.html", status=status, username=username)

# удаление сессии
@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return redirect(url_for('index'))

# панель администратора
@app.route('/admin')
def admin():
    return render_template("admin.html")

# админка, работа с данными
@app.route('/admin_data')
def adminData():
    return render_template("admin_data.html")

# АДМИНКА, ОТРАСЛИ И ДОЛЖНОСТИ
@app.route('/admin_data_ip')
def adminDataIP():
    return render_template("admin_data_ip.html")

# добавление
@app.route('/admin_data_ip_add', methods=['GET', 'POST'])
def adminDataIPAdd():
    industries = selectColumn('industry_name', 'industry_profession')
    professions = selectColumn('profession_name', 'industry_profession')

    if request.method == 'POST':
        industry = request.form.get('industry')
        profession = request.form.get('profession')

        if industry == '' or profession == '':
            return render_template("admin_data_ip_add.html", message='Не введена отрасль или дожность!')
        else:
            try:
                if industry not in industries:
                    cur.execute("insert into industry (industry_name) values (%s)", (industry, ))
                    conn.commit()
                if profession not in professions:
                    cur.execute("insert into profession (profession_name) values (%s)", (profession, ))
                    conn.commit()
                cur.execute("insert into industry_profession (industry_name, profession_name) values (%s, %s)", (industry, profession, ))
                conn.commit()
                return redirect(url_for('adminDataIPAdd'))
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("admin_data_ip_add.html", message='Данная отрасль или должность уже существует!', industries=industries, professions=professions)
    return render_template("admin_data_ip_add.html", industries=industries, professions=professions)

# изменение
@app.route('/admin_data_ind_edit', methods=['GET', 'POST'])
def adminDataIndEdit():
    industries = selectColumn('industry_name', 'industry')

    if request.method == 'POST':
        industryOld = request.form.get('old_industry')
        industryNew = request.form.get('new_industry')

        if industryOld == '' or industryNew == '':
            return render_template("admin_data_ind_edit.html", message='Введите название отрасли!')
        else:
            try:
                cur.execute("update industry set industry_name = %s WHERE industry_name = %s",
                            (industryNew, industryOld))
                conn.commit()
                return redirect(url_for('adminDataIndEdit'))
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("admin_data_ind_edit.html",
                                       message='Данная отрасль уже существует!')
    return render_template("admin_data_ind_edit.html", industries=industries)

# АДМИНКА, СФЕРЫ ДЕЯТЕЛЬНОСТИ
@app.route('/admin_data_areas')
def adminDataAreas():
    return render_template("admin_data_areas.html")

# добавление
@app.route('/admin_data_areas_add', methods=['GET', 'POST'])
def adminDataAreasAdd():
    areas = selectColumn('area_name', 'area')

    if request.method == 'POST':
        area = request.form.get('area')

        if area != '':
            try:
                cur.execute("insert into area (area_name) values (%s)", (area, ))
                conn.commit()
                return redirect(url_for('adminDataAreasAdd'))
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("admin_data_areas_add.html", message='Данная сфера деятельности уже существует!')
        else:
            return render_template("admin_data_areas_add.html", message='Не введена сфера деятельности!')
    return render_template("admin_data_areas_add.html", areas=areas)

# изменение
@app.route('/admin_data_areas_edit', methods=['GET', 'POST'])
def adminDataAreasEdit():
    areas = selectColumn('area_name', 'area')

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
    return render_template("admin_data_areas_edit.html", areas=areas)

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
