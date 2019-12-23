import os
from datetime import date

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

@app.route('/guest_mode')
def guestMode():
    return render_template("guest_mode.html")

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
    areas = selectColumn('area_name', 'area')

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

                vacPubData = date.today()

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

        if status == 'employee':
            if request.method == 'POST':
                industryName = request.form.get('industry_name')
                professionName = request.form.get('profession_name')
                minSalary = request.form.get('min_salary')
                maxSalary = request.form.get('max_salary')
                exp = request.form.get('exp')
                empType = request.form.get('emp_type')

                cvPubData = date.today()

                if minSalary == '':
                    minSalary = None
                elif maxSalary == '':
                    maxSalary = None

                try:
                    if industryName == '' or professionName == '' or exp == '' or empType == '':
                        return render_template("create_item.html", message='Пожайлуста, заполните все поля',
                                           status=status, username=username, industries=industries,
                                           professions=professions)
                    else:
                        cur.execute(
                        "insert into cv (user_id, industry_name, profession_name, min_salary, max_salary, exp, emp_type, cv_pub_data) values (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (userID, industryName, professionName, minSalary, maxSalary, exp, empType, cvPubData))
                        conn.commit()
                except psycopg2.errors.InvalidTextRepresentation:
                    conn.rollback()
                    return render_template("create_item.html", message='В численные поля записан текст!',
                                           status=status, username=username, industries=industries,
                                           professions=professions)
                return redirect(url_for('itemList', status=status, username=username))

        if status == 'customer':
            if request.method == 'POST':
                areaName = request.form.get('area_name')
                taskDescr = request.form.get('task_descr')
                day = request.form.get('day')
                month = request.form.get('month')
                year = request.form.get('year')
                price = request.form.get('price')

                try:
                    dayNum = int(day)
                    monthNum = int(month)
                    yearNum = int(year)
                except ValueError:
                    return render_template("create_item.html", message='Дата выполнения заполнена неправильно!',
                                           status=status, username=username, areas=areas)

                execDate = date(yearNum, monthNum, dayNum)
                today = date.today()

                if execDate < today:
                    return render_template("create_item.html", message='Дата выполнения не может быть раньше сегодняшней',
                                           status=status, username=username, areas=areas)

                try:
                    if areaName == '' or taskDescr == '' or execDate == '' or price == '':
                        return render_template("create_item.html", message='Пожайлуста, заполните все поля',
                                               status=status, username=username, areas=areas)
                    else:
                        cur.execute(
                            "insert into task (user_id, area_name, task_descr, exec_date, price) values (%s, %s, %s, %s, %s)",
                            (userID, areaName, taskDescr, execDate, price))
                        conn.commit()
                except psycopg2.errors.InvalidTextRepresentation:
                    conn.rollback()
                    return render_template("create_item.html", message='В численные поля записан текст!',
                                           status=status, username=username, areas=areas)
                return redirect(url_for('itemList', status=status, username=username))
    return render_template("create_item.html", status=status, username=username, industries=industries, professions=professions, areas=areas)

# список записей
@app.route('/item_list/<status>/<username>')
def itemList(status, username):
    if g.user:
        viewsCount = []

        userID = getUserID(username)

        cur.execute('SELECT vacancy_id, industry_name, profession_name, employee_sex, min_emp_age, max_emp_age, min_salary, min_exp, emp_type, vac_pub_data FROM vacancy WHERE user_id = %s', (userID,))
        vacancyInfo = cur.fetchall()
        conn.commit()

        cur.execute('SELECT cv_id, industry_name, profession_name, min_salary, max_salary, exp, emp_type, cv_pub_data FROM cv WHERE user_id = %s', (userID,))
        cvInfo = cur.fetchall()
        cvInfo = [list(elem) for elem in cvInfo]
        conn.commit()

        cur.execute('SELECT cv_id FROM cv WHERE user_id = %s', (userID,))
        cvIDs = cur.fetchall()
        cvIDs = list(sum(cvIDs, ()))
        conn.commit()

        for item in cvIDs:
            cur.execute('SELECT count(*) FROM browsing WHERE cv_id = (select cv_id from cv where cv_id = %s)', (item,))
            result = cur.fetchone()
            viewsCount.append(result[0])
            conn.commit()

        for f, b in list(zip(cvInfo, viewsCount)):
            f.append(b)

        cur.execute('SELECT task_id, area_name, task_descr, exec_date, price FROM task WHERE user_id = %s', (userID,))
        taskInfo = cur.fetchall()
        conn.commit()
    return render_template("item_list.html", status=status, username=username, vacancyInfo=vacancyInfo, cvInfo=cvInfo, taskInfo=taskInfo)

# изменение записи
@app.route('/edititem/<status>/<username>/<itemid>', methods=['GET', 'POST'])
def editItem(status, username, itemid):
    industries = selectColumn('industry_name', 'industry')
    professions = selectColumn('profession_name', 'profession')
    areas = selectColumn('area_name', 'area')

    if g.user:
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

                if industryName != None:
                    cur.execute('update vacancy set industry_name = %s WHERE vacancy_id = %s', (industryName, itemid,))
                if professionName != None:
                    cur.execute('update vacancy set profession_name = %s WHERE vacancy_id = %s',
                                (professionName, itemid,))
                if employeeSex != None:
                    cur.execute('update vacancy set employee_sex = %s WHERE vacancy_id = %s', (employeeSex, itemid,))
                if minEmpAge != '':
                    cur.execute('update vacancy set min_emp_age = %s WHERE vacancy_id = %s', (minEmpAge, itemid,))
                if maxEmpAge != '':
                    cur.execute('update vacancy set max_emp_age = %s WHERE vacancy_id = %s', (maxEmpAge, itemid,))
                if minSalary != '':
                    cur.execute('update vacancy set min_salary = %s WHERE vacancy_id = %s', (minSalary, itemid,))
                if minExp != '':
                    cur.execute('update vacancy set min_exp = %s WHERE vacancy_id = %s', (minExp, itemid,))
                if empType != None:
                    cur.execute('update vacancy set emp_type = %s WHERE vacancy_id = %s', (empType, itemid,))
                conn.commit()
                return redirect(url_for('itemList', status=status, username=username))

        if status == 'employee':
            if request.method == 'POST':
                industryName = request.form.get('industry_name')
                professionName = request.form.get('profession_name')
                minSalary = request.form.get('min_salary')
                maxSalary = request.form.get('max_salary')
                exp = request.form.get('exp')
                empType = request.form.get('emp_type')

                if industryName != None:
                    cur.execute('update cv set industry_name = %s WHERE cv_id = %s', (industryName, itemid,))
                if professionName != None:
                    cur.execute('update cv set profession_name = %s WHERE cv_id = %s', (professionName, itemid,))
                if minSalary != '':
                    cur.execute('update cv set min_salary = %s WHERE cv_id = %s', (minSalary, itemid,))
                if maxSalary != '':
                    cur.execute('update cv set max_salary = %s WHERE cv_id = %s', (maxSalary, itemid,))
                if exp != '':
                    cur.execute('update cv set exp = %s WHERE cv_id = %s', (exp, itemid,))
                if empType != None:
                    cur.execute('update cv set emp_type = %s WHERE cv_id = %s', (empType, itemid,))
                conn.commit()
                return redirect(url_for('itemList', status=status, username=username))

        if status == 'customer':
            if request.method == 'POST':
                areaName = request.form.get('area_name')
                taskDescr = request.form.get('task_descr')
                day = request.form.get('day')
                month = request.form.get('month')
                year = request.form.get('year')
                price = request.form.get('price')

                if areaName != None:
                    cur.execute('update task set area_name = %s WHERE task_id = %s', (areaName, itemid,))
                if taskDescr != '':
                    cur.execute('update task set task_descr = %s WHERE task_id = %s', (taskDescr, itemid,))
                if day != '' or month != '' or year != '':
                    try:
                        dayNum = int(day)
                        monthNum = int(month)
                        yearNum = int(year)
                    except ValueError:
                        return render_template("create_item.html", message='Дата выполнения заполнена неправильно!',
                                               status=status, username=username, areas=areas)

                    execDate = date(yearNum, monthNum, dayNum)
                    today = date.today()

                    if execDate < today:
                        return render_template("create_item.html",
                                               message='Дата выполнения не может быть раньше сегодняшней',
                                               status=status, username=username, areas=areas)

                    cur.execute('update task set exec_date = %s WHERE task_id = %s', (execDate, itemid,))
                if price != '':
                    cur.execute('update task set price = %s WHERE task_id = %s', (price, itemid,))
                conn.commit()
                return redirect(url_for('itemList', status=status, username=username))
    return render_template("edit_item.html", status=status, username=username, itemid=itemid, industries=industries, professions=professions, areas=areas)

# удаление записи
@app.route('/deleteitem/<status>/<username>/<itemid>', methods=['POST'])
def deleteItem(status, username, itemid):
    if g.user:
        if status == 'company':
            cur.execute('delete from vacancy where vacancy_id = %s', (itemid,))
            conn.commit()

        if status == 'employee':
            cur.execute('delete from cv where cv_id = %s', (itemid,))
            conn.commit()
    return redirect(url_for('itemList', status=status, username=username))

# КАТАЛОГ РЕЗЮМЕ
# отрасли
@app.route('/cv_cat_ind/<username>')
def cvCatInd(username):
    if g.user:
        counts = []

        cur.execute('SELECT industry_name FROM industry_profession WHERE industry_name in (select industry_name from cv) group by industry_name')
        industries = cur.fetchall()
        conn.commit()

        industries = list(sum(industries, ()))

        for item in industries:
            cur.execute('SELECT count(*) FROM cv WHERE industry_name = %s', (item,))
            count = cur.fetchone()
            counts.append(count)
            conn.commit()

        counts = list(sum(counts, ()))

        data = list(zip(industries, counts))
    return render_template("cv_cat_ind.html", username=username, data=data)

# должности
@app.route('/cv_cat_pro/<username>/<industry>')
def cvCatPro(username, industry):
    if g.user:
        counts = []

        cur.execute('SELECT profession_name FROM industry_profession WHERE industry_name = %s group by profession_name', (industry,))
        professions = cur.fetchall()
        conn.commit()

        professions = list(sum(professions, ()))

        for item in professions:
            cur.execute('SELECT count(*) FROM cv WHERE profession_name = %s', (item,))
            count = cur.fetchone()
            counts.append(count)
            conn.commit()

        counts = list(sum(counts, ()))

        data = list(zip(professions, counts))
    return render_template("cv_cat_pro.html", username=username, data=data, industry=industry)

# список резюме
@app.route('/cv_cat_list/<username>/<industry>/<profession>')
def cvCatList(username, industry, profession):
    userID = getUserID(username)

    if g.user:
        cur.execute('SELECT cv_id, industry_name, profession_name, min_salary, max_salary, exp, emp_type, cv_pub_data FROM cv WHERE industry_name = %s and profession_name = %s', (industry, profession))
        cvInfo = cur.fetchall()
        conn.commit()
    return render_template("cv_cat_list.html", username=username, cvInfo=cvInfo, userid=userID, industry=industry, profession=profession)

# резюме полностью
@app.route('/cv_cat_item/<industry>/<profession>/<userid>/<itemid>')
def cvCatItem(userid, itemid, industry, profession):
    if g.user:
        data = date.today()

        cur.execute("insert into browsing (user_id, cv_id, view_data) values (%s, %s, %s)", (userid, itemid, data))
        conn.commit()

        cur.execute('SELECT * FROM cv WHERE industry_name = %s and profession_name = %s', (industry, profession))
        result = cur.fetchall()
        cvInfo = list(sum(result , ()))
        conn.commit()

        cur.execute('SELECT full_name FROM employee WHERE user_id = (select user_id from cv where cv_id = %s)', (itemid,))
        result = cur.fetchone()
        fullName = result[0]
        conn.commit()

        cur.execute('SELECT email, phone FROM person WHERE user_id = (select user_id from cv where cv_id = %s)', (itemid,))
        result = cur.fetchall()
        contacts = list(sum(result , ()))
        conn.commit()
    return render_template("cv_cat_item.html", itemid=itemid, userid=userid, cvInfo=cvInfo, fullName=fullName, contacts=contacts)

# КАТАЛОГ ВАКАНСИЙ
# отрасли
@app.route('/vacancy_cat_ind/')
def vacCatInd():
    counts = []

    cur.execute('SELECT industry_name FROM industry_profession WHERE industry_name in (select industry_name from vacancy) group by industry_name')
    industries = cur.fetchall()
    conn.commit()

    industries = list(sum(industries, ()))

    for item in industries:
        cur.execute('SELECT count(*) FROM vacancy WHERE industry_name = %s', (item,))
        count = cur.fetchone()
        counts.append(count)
        conn.commit()

    counts = list(sum(counts, ()))

    data = list(zip(industries, counts))
    return render_template("vacancy_cat_ind.html", data=data)

# должности
@app.route('/vacancy_cat_pro/<industry>')
def vacCatPro(industry):
    counts = []

    cur.execute('SELECT profession_name FROM industry_profession WHERE industry_name = %s group by profession_name', (industry,))
    professions = cur.fetchall()
    conn.commit()

    professions = list(sum(professions, ()))

    for item in professions:
        cur.execute('SELECT count(*) FROM vacancy WHERE profession_name = %s', (item,))
        count = cur.fetchone()
        counts.append(count)
        conn.commit()

    counts = list(sum(counts, ()))

    data = list(zip(professions, counts))
    return render_template("vacancy_cat_pro.html", data=data, industry=industry)

# список вакансий
@app.route('/vacancy_cat_list/<industry>/<profession>')
def vacCatList(industry, profession):
    cur.execute('SELECT vacancy_id, industry_name, profession_name, employee_sex, min_emp_age, max_emp_age, min_salary, min_exp, emp_type, vac_pub_data FROM vacancy WHERE industry_name = %s and profession_name = %s', (industry, profession))
    vacancyInfo = cur.fetchall()
    conn.commit()
    return render_template("vacancy_cat_list.html", vacancyInfo=vacancyInfo, industry=industry, profession=profession)

# вакансия полностью
@app.route('/vacancy_cat_item/<industry>/<profession>/<itemid>')
def vacCatItem(itemid, industry, profession):
    cur.execute('SELECT vacancy_id, industry_name, profession_name, employee_sex, min_emp_age, max_emp_age, min_salary, min_exp, emp_type, vac_pub_data FROM vacancy WHERE industry_name = %s and profession_name = %s', (industry, profession))
    result = cur.fetchall()
    vacancyInfo = list(sum(result , ()))
    conn.commit()

    cur.execute('SELECT company_name FROM company WHERE user_id = (select user_id from vacancy where vacancy_id = %s)', (itemid,))
    result = cur.fetchone()
    companyName = result[0]
    conn.commit()

    cur.execute('SELECT email, phone FROM person WHERE user_id = (select user_id from vacancy where vacancy_id = %s)', (itemid,))
    result = cur.fetchall()
    contacts = list(sum(result , ()))
    conn.commit()
    return render_template("vacancy_cat_item.html", itemid=itemid, vacancyInfo=vacancyInfo, companyName=companyName, contacts=contacts)

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

# АДМИНКА, УДАЛЕНИЕ
# удаление резюме
@app.route('/admin_delete_cv', methods=['GET', 'POST'])
def adminDeleteCv():
    if request.method == 'POST':
        day = request.form.get('day')
        month = request.form.get('month')
        year = request.form.get('year')

        try:
            dayNum = int(day)
            monthNum = int(month)
            yearNum = int(year)
        except ValueError:
            return render_template("admin_delete_cv.html", message="Введено не целочисленное значение!")

        dateInput = date(yearNum, monthNum, dayNum)

        cur.execute('delete from cv where cv_pub_data::date < %s::date', (dateInput,))
        conn.commit()
    return render_template("admin_delete_cv.html")

# удаление вакансий
@app.route('/admin_delete_vacancy', methods=['GET', 'POST'])
def adminDeleteVacancy():
    if request.method == 'POST':
        day = request.form.get('day')
        month = request.form.get('month')
        year = request.form.get('year')

        try:
            dayNum = int(day)
            monthNum = int(month)
            yearNum = int(year)
        except ValueError:
            return render_template("admin_delete_vacancy.html", message="Введено не целочисленное значение!")

        dateInput = date(yearNum, monthNum, dayNum)

        cur.execute('delete from vacancy where vac_pub_data::date < %s::date', (dateInput,))
        conn.commit()
    return render_template("admin_delete_vacancy.html")

# удаление заданий
@app.route('/admin_delete_task', methods=['GET', 'POST'])
def adminDeleteTask():
    if request.method == 'POST':
        day = request.form.get('day')
        month = request.form.get('month')
        year = request.form.get('year')

        try:
            dayNum = int(day)
            monthNum = int(month)
            yearNum = int(year)
        except ValueError:
            return render_template("admin_delete_task.html", message="Введено не целочисленное значение!")

        dateInput = date(yearNum, monthNum, dayNum)

        cur.execute('delete from task where exec_date::date < %s::date', (dateInput,))
        conn.commit()
    return render_template("admin_delete_task.html")

@app.route('/vacancy_cat')
def vacancyCat():
    vacancies = ["Engineer", "Programmist", "Cleaner"]
    return render_template("vacancy_cat.html", vacancies=vacancies)

if __name__ == '__main__':
    app.run(debug=True)
