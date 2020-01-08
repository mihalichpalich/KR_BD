import os
from datetime import datetime, date

from flask import *
from flask_bootstrap import Bootstrap

from forms import *

app = Flask(__name__)
app.secret_key = os.urandom(24)
Bootstrap(app)

createDatabase()
createAdmin()

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
    form = SignUpForm()

    if form.validate_on_submit():
        login = form.login.data
        password = form.password.data
        status = form.status.data
        email = form.email.data
        phone = form.phone.data

        passwordHash = generate_password_hash(password)

        try:
            cur.execute("insert into person (login, password, status, email, phone) values (%s, %s, %s, %s, %s)", (login, passwordHash, status, email, phone))
            conn.commit()
            return redirect(url_for('success'))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            return render_template("sign_up.html", message='Пользователь с данным логином, email или телефоном уже существует!', form=form)
    return render_template("sign_up.html", form=form)

# успешная регистрация
@app.route('/success', methods=['GET', 'POST'])
def success():
    return render_template("success.html")

# вход
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        session.pop('user', None)

        username = form.login.data
        password = form.password.data

        cur.execute('SELECT user_id, password, status FROM person WHERE login = %s', (username, ))
        if cur.rowcount == 0:
            return render_template("login.html", message='Пользователя с данным логином не существует!', form=form)
        result = cur.fetchone()
        user_id = result[0]
        passwordHash = result[1]
        status = result[2]
        conn.commit()

        if username == 'admin' and password == 'admin':
            session['user'] = user_id
            return redirect(url_for('admin'))

        resultHash = check_password_hash(passwordHash, password)
        if not resultHash:
            return render_template("login.html", message='Введен неправильный пароль!', form=form)

        session['user'] = user_id
        return redirect(url_for('profile', status=status, username=username))
    return render_template("login.html", form=form)

# восстановление пароля
@app.route('/pw_rec', methods=['GET', 'POST'])
def pwRec():
    form = PwRecForm()

    if form.validate_on_submit():
        login = form.login.data
        passwordOld = form.passwordOld.data
        passwordNew = form.passwordNew.data

        cur.execute('SELECT * FROM person WHERE login = %s', (login, ))
        if cur.rowcount == 0:
            return render_template("pw_rec.html", message='Пользователя с данным логином не существует!', form=form)
        conn.commit()

        if passwordOld != passwordNew:
            return render_template("pw_rec.html", message='Пароли не совпадают!', form=form)

        passwordHash = generate_password_hash(passwordNew)

        cur.execute('update person set password = %s WHERE login = %s', (passwordHash, login, ))
        conn.commit()

        return redirect(url_for('pwRecSuc'))
    return render_template("pw_rec.html", form=form)

# успешное восстановление пароля
@app.route('/pw_rec_suc', methods=['GET', 'POST'])
def pwRecSuc():
    return render_template("pw_rec_suc.html")

# страница профиля
@app.route('/profile/<status>/<username>', methods=['GET', 'POST'])
def profile(status, username):
    if g.user:
        warning = ''

        if status == 'company':
            inn = loadInfoFromProfile('inn', 'company', username)
            companyName = loadInfoFromProfile('company_name', 'company', username)
            companyPhone = loadInfoFromPerson('phone', username)
            companyEmail = loadInfoFromPerson('email', username)

            if inn == '' or companyName == '':
                warning = True
            return render_template("profile.html", status=status, username=username, inn=inn, companyName=companyName,
                                   companyPhone=companyPhone, companyEmail=companyEmail, warning=warning)

        if status == 'employee':
            fullName = loadInfoFromProfile('full_name', 'employee', username)
            employeePhone = loadInfoFromPerson('phone', username)
            employeeEmail = loadInfoFromPerson('email', username)

            if fullName == '':
                warning = True
            return render_template("profile.html", status=status, username=username, fullName=fullName,
                                   employeePhone=employeePhone, employeeEmail=employeeEmail, warning=warning)

        if status == 'customer':
            customerName = loadInfoFromProfile('customer_name', 'customer', username)
            customerPhone = loadInfoFromPerson('phone', username)
            customerEmail = loadInfoFromPerson('email', username)

            if customerName == '':
                warning = True
            return render_template("profile.html", status=status, username=username, customerName=customerName,
                                   customerPhone=customerPhone, customerEmail=customerEmail, warning=warning)

        if status == 'performer':
            performerName = loadInfoFromProfile('performer_name', 'performer', username)
            performerArea = loadInfoFromProfile('area_name', 'performer', username)
            servicesDescr = loadInfoFromProfile('services_descr', 'performer', username)
            performerPhone = loadInfoFromPerson('phone', username)
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
    userID = getUserID(username)

    cur.execute('SELECT email, phone FROM person WHERE user_id = %s', (userID,))
    result = cur.fetchall()
    print(result)
    contacts = []
    if result:
        contacts = list(sum(result, ()))
    conn.commit()

    cur.execute('SELECT inn, company_name FROM company WHERE user_id = %s', (userID,))
    result = cur.fetchall()
    companyInfo = []
    if result:
        companyInfo = list(sum(result, ()))
    conn.commit()

    cur.execute('SELECT full_name FROM employee WHERE user_id = %s', (userID,))
    result = cur.fetchone()
    employeeInfo = []
    if result is not None:
        employeeInfo = result[0]
    conn.commit()

    cur.execute('SELECT customer_name FROM customer WHERE user_id = %s', (userID,))
    result = cur.fetchone()
    customerInfo = ''
    if result is not None:
        customerInfo = result[0]
    conn.commit()

    cur.execute('SELECT performer_name, area_name, services_descr FROM performer WHERE user_id = %s', (userID,))
    result = cur.fetchall()
    performerInfo = []
    if result:
        performerInfo = list(sum(result, ()))
    conn.commit()

    if companyInfo:
        formCompany = ProfEdCompanyForm(inn=companyInfo[0], companyName=companyInfo[1], companyEmail=contacts[0], companyPhone=contacts[1])
    else:
        formCompany = []

    formEmployee = ProfEdEmployeeForm(fullName=employeeInfo, employeeEmail=contacts[0], employeePhone=contacts[1])
    formCustomer = ProfEdCustomerForm(customerName=customerInfo, customerEmail=contacts[0], customerPhone=contacts[1])

    if performerInfo:
        formPerformer = ProfEdPerformerForm(performerName=performerInfo[0], performerArea=performerInfo[1], servicesDescr=performerInfo[2], performerEmail=contacts[0], performerPhone=contacts[1])
    else:
        formPerformer = []

    if g.user:
        if status == 'company' and formCompany.validate_on_submit():
            inn = formCompany.inn.data
            companyName = formCompany.companyName.data
            companyPhone = formCompany.companyPhone.data
            companyEmail = formCompany.companyEmail.data

            isCompany = userExist('company', userID)

            try:
                if isCompany == 0:
                    if inn == '' or companyName == '':
                        return render_template("profile_edit.html", message='Пожайлуста, введите ИНН и название компании', status=status, username=username, formCompany=formCompany)
                    cur.execute("insert into company (user_id, inn, company_name) values (%s, %s, %s)",
                                (userID, inn, companyName,))
                else:
                    if inn != '':
                        cur.execute('update company set inn = %s WHERE user_id = %s', (inn, userID,))
                    if companyName != '':
                        cur.execute('update company set company_name = %s WHERE user_id = %s', (companyName, userID,))
                    if companyPhone != '':
                        cur.execute('update person set phone = %s WHERE user_id = %s', (companyPhone, userID,))
                    if companyEmail != '':
                        cur.execute('update person set email = %s WHERE user_id = %s', (companyEmail, userID,))
                conn.commit()
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("profile_edit.html",
                                       message='Пользователь с данным ИНН, телефоном или email уже существует!',
                                       status=status, username=username, formCompany=formCompany)
            except psycopg2.errors.StringDataRightTruncation:
                conn.rollback()
                return render_template("profile_edit.html", message='ИНН должен состоять не более чем из 10 символов!',
                                       status=status, username=username, formCompany=formCompany)
            return redirect(url_for('profile', status=status, username=username))

        if status == 'employee' and formEmployee.validate_on_submit():
            fullName = formEmployee.fullName.data
            employeePhone = formEmployee.employeePhone.data
            employeeEmail = formEmployee.employeeEmail.data

            isEmployee = userExist('employee', userID)

            try:
                if isEmployee == 0:
                    if fullName == '':
                        return render_template("profile_edit.html", message='Пожайлуста, введите ФИО', status=status, username=username, formEmployee=formEmployee)
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
                return render_template("profile_edit.html", message='Пользователь с данным телефоном или email уже существует!', status=status, username=username, formEmployee=formEmployee)
            return redirect(url_for('profile', status=status, username=username))

        if status == 'customer' and formCustomer.validate_on_submit():
            customerName = formCustomer.customerName.data
            customerPhone = formCustomer.customerPhone.data
            customerEmail = formCustomer.customerEmail.data

            isCustomer = userExist('customer', userID)

            try:
                if isCustomer == 0:
                    if customerName == '':
                        return render_template("profile_edit.html", message='Пожайлуста, введите Ваше имя', status=status, username=username, formCustomer=formCustomer)
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
                return render_template("profile_edit.html", message='Пользователь с данным телефоном или email уже существует!', status=status, username=username, formCustomer=formCustomer)
            return redirect(url_for('profile', status=status, username=username, formCustomer=formCustomer))

        if status == 'performer' and formPerformer.validate_on_submit():
            performerName = formPerformer.performerName.data
            performerArea = formPerformer.performerArea.data
            servicesDescr = formPerformer.servicesDescr.data
            performerPhone = formPerformer.performerPhone.data
            performerEmail = formPerformer.performerEmail.data

            isPerformer = userExist('performer', userID)

            try:
                if isPerformer == 0:
                    if performerName == '' or performerArea == '' or servicesDescr == '':
                        return render_template("profile_edit.html",
                                               message='Пожайлуста, введите Ваше имя, сферу деятельности и описание услуг',
                                               status=status, username=username, formPerformer=formPerformer)
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
                return render_template("profile_edit.html", message='Пользователь с данным телефоном или email уже существует!', status=status, username=username, formPerformer=formPerformer)
            return redirect(url_for('profile', status=status, username=username))
        return render_template("profile_edit.html", status=status, username=username, formPerformer=formPerformer, formCompany=formCompany, formEmployee=formEmployee, formCustomer=formCustomer)
    return render_template("profile_edit.html", status=status, username=username, formCompany=formCompany, formEmployee=formEmployee, formCustomer=formCustomer, formPerformer=formPerformer)

# добавление записи
@app.route('/create_item/<status>/<username>', methods=['GET', 'POST'])
def createItem(status, username):
    formCompany = CreateItemCompanyForm()
    formEmployee = CreateItemEmployeeForm()
    formCustomer = CreateItemCustomerForm()

    if g.user:
        userID = getUserID(username)

        if status == 'company' and formCompany.validate_on_submit():
            industryName = formCompany.industryName.data
            professionName = formCompany.professionName.data
            employeeSex = formCompany.employeeSex.data
            minEmpAge = formCompany.minEmpAge.data
            maxEmpAge = formCompany.maxEmpAge.data
            minSalary = formCompany.minSalary.data
            minExp = formCompany.minExp.data
            empType = formCompany.empType.data

            vacPubData = date.today()

            if maxEmpAge == '':
                maxEmpAge = None
            if minExp == 0:
                minExp = 'без опыта'

            try:
                cur.execute(
                    "insert into vacancy (user_id, industry_name, profession_name, employee_sex, min_emp_age, max_emp_age, min_salary, min_exp, emp_type, vac_pub_data) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (userID, industryName, professionName, employeeSex, minEmpAge,
                     maxEmpAge, minSalary, minExp, empType, vacPubData))
                conn.commit()
            except psycopg2.errors.InvalidTextRepresentation:
                conn.rollback()
                return render_template("create_item.html", message='В численные поля записан текст!', status=status, username=username, formCompany=formCompany)
            return redirect(url_for('itemList', status=status, username=username))

        if status == 'employee' and formEmployee.validate_on_submit():
            industryName = formEmployee.industryName.data
            professionName = formEmployee.professionName.data
            minSalary = formEmployee.minSalary.data
            maxSalary = formEmployee.maxSalary.data
            exp = formEmployee.exp.data
            empType = formEmployee.empType.data

            cvPubData = date.today()

            if minSalary == '':
                minSalary = None
            elif maxSalary == '':
                maxSalary = None
            if exp == 0:
                exp = 'без опыта'

            try:
                cur.execute(
                "insert into cv (user_id, industry_name, profession_name, min_salary, max_salary, exp, emp_type, cv_pub_data) values (%s, %s, %s, %s, %s, %s, %s, %s)",
                (userID, industryName, professionName, minSalary, maxSalary, exp, empType, cvPubData))
                conn.commit()
            except psycopg2.errors.InvalidTextRepresentation:
                conn.rollback()
                return render_template("create_item.html", message='В численные поля записан текст!', status=status, username=username, formEmployee=formEmployee)
            return redirect(url_for('itemList', status=status, username=username))

        if status == 'customer' and formCustomer.validate_on_submit():
            areaName = formCustomer.areaName.data
            taskDescr = formCustomer.taskDescr.data
            dateInput = formCustomer.dateInput.data
            price = formCustomer.price.data

            today = date.today()

            if dateInput < today:
                return render_template("create_item.html", message='Дата выполнения не может быть раньше сегодняшней',
                                       status=status, username=username, formCustomer=formCustomer)

            try:
                cur.execute(
                    "insert into task (user_id, area_name, task_descr, exec_date, price) values (%s, %s, %s, %s, %s)",
                    (userID, areaName, taskDescr, dateInput, price))
                conn.commit()
            except psycopg2.errors.InvalidTextRepresentation:
                conn.rollback()
                return render_template("create_item.html", message='В численные поля записан текст!',
                                       status=status, username=username, formCustomer=formCustomer)
            return redirect(url_for('itemList', status=status, username=username))
    return render_template("create_item.html", status=status, username=username, formCompany=formCompany, formEmployee=formEmployee, formCustomer=formCustomer)

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
    formCompany = []
    formEmployee = []
    formCustomer = []

    if g.user:
        if status == 'company':
            cur.execute(
                'SELECT industry_name, profession_name, employee_sex, min_emp_age, max_emp_age, min_salary, min_exp, emp_type FROM vacancy WHERE vacancy_id = %s',
                (itemid))
            vacancyInfo = cur.fetchall()
            vacancyInfo = list(sum(vacancyInfo, ()))
            conn.commit()

            for i in range(len(vacancyInfo)):
                if vacancyInfo[i] is None:
                    vacancyInfo[i] = ''
            if vacancyInfo[6] == 'без опыта':
                vacancyInfo[6] = 0

            formCompany = CreateItemCompanyForm(industryName=vacancyInfo[0], professionName=vacancyInfo[1],
                                                employeeSex=vacancyInfo[2], minEmpAge=vacancyInfo[3],
                                                maxEmpAge=vacancyInfo[4], minSalary=vacancyInfo[5],
                                                minExp=vacancyInfo[6], empType=vacancyInfo[7])

            if formCompany.validate_on_submit():
                industryName = formCompany.industryName.data
                professionName = formCompany.professionName.data
                employeeSex = formCompany.employeeSex.data
                minEmpAge = formCompany.minEmpAge.data
                maxEmpAge = formCompany.maxEmpAge.data
                minSalary = formCompany.minSalary.data
                minExp = formCompany.minExp.data
                empType = formCompany.empType.data

                if maxEmpAge == '':
                    maxEmpAge = None
                if minExp == 0:
                    minExp = 'без опыта'

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
            cur.execute(
                'SELECT industry_name, profession_name, min_salary, max_salary, exp, emp_type FROM cv WHERE cv_id = %s',
                (itemid))
            cvInfo = cur.fetchall()
            cvInfo = list(sum(cvInfo, ()))
            conn.commit()

            for i in range(len(cvInfo)):
                if cvInfo[i] is None:
                    cvInfo[i] = ''
            if cvInfo[4] == 'без опыта':
                cvInfo[4] = 0

            formEmployee = CreateItemEmployeeForm(industryName=cvInfo[0], professionName=cvInfo[1], minSalary=cvInfo[2],
                                                  maxSalary=cvInfo[3], exp=cvInfo[4], empType=cvInfo[5])

            if formEmployee.validate_on_submit():
                industryName = formEmployee.industryName.data
                professionName = formEmployee.professionName.data
                minSalary = formEmployee.minSalary.data
                maxSalary = formEmployee.maxSalary.data
                exp = formEmployee.exp.data
                empType = formEmployee.empType.data

                if minSalary == '':
                    minSalary = None
                elif maxSalary == '':
                    maxSalary = None
                if exp == 0:
                    exp = 'без опыта'

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
            cur.execute('SELECT area_name, task_descr, exec_date, price FROM task WHERE task_id = %s', (itemid))
            taskInfo = cur.fetchall()
            taskInfo = list(sum(taskInfo, ()))
            conn.commit()

            datetime_obj = datetime.strptime(taskInfo[2], "%Y-%m-%d")
            taskInfo[2] = datetime_obj.date()

            formCustomer = CreateItemCustomerForm(areaName=taskInfo[0], taskDescr=taskInfo[1], dateInput=taskInfo[2], price=taskInfo[3])

            if formCustomer.validate_on_submit():
                areaName = formCustomer.areaName.data
                taskDescr = formCustomer.taskDescr.data
                dateInput = formCustomer.dateInput.data
                price = formCustomer.price.data

                today = date.today()

                if areaName != None:
                    cur.execute('update task set area_name = %s WHERE task_id = %s', (areaName, itemid,))
                if taskDescr != '':
                    cur.execute('update task set task_descr = %s WHERE task_id = %s', (taskDescr, itemid,))
                if dateInput != '':
                    if dateInput < today:
                        return render_template("edit_item.html",
                                               message='Дата выполнения не может быть раньше сегодняшней',
                                               status=status, username=username, formCustomer=formCustomer)
                        cur.execute('update task set exec_date = %s WHERE task_id = %s', (execDate, itemid,))
                if price != '':
                    cur.execute('update task set price = %s WHERE task_id = %s', (price, itemid,))
                conn.commit()
                return redirect(url_for('itemList', status=status, username=username))
    return render_template("edit_item.html", status=status, username=username, itemid=itemid, formCompany=formCompany, formEmployee=formEmployee, formCustomer=formCustomer)

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

        if status == 'customer':
            cur.execute('delete from task where task_id = %s', (itemid,))
            conn.commit()
    return redirect(url_for('itemList', status=status, username=username))

# КАТАЛОГ РЕЗЮМЕ
# отрасли
@app.route('/cv_cat_ind/<username>')
def cvCatInd(username):
    if g.user:
        counts = []
        industriesURL = []

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

        for item in industries:
            itemUni = translitToURL(item)
            industriesURL.append(itemUni)

        data = list(zip(industries, counts, industriesURL))
    return render_template("cv_cat_ind.html", username=username, data=data)

# должности
@app.route('/cv_cat_pro/<username>/<industryURL>')
def cvCatPro(username, industryURL):
    if g.user:
        counts = []
        professionsURL = []
        industry = translitFromURL(industryURL)

        cur.execute('SELECT profession_name FROM industry_profession WHERE profession_name in (select profession_name from cv where industry_name = %s)', (industry,))
        professions = cur.fetchall()
        conn.commit()

        professions = list(sum(professions, ()))

        for item in professions:
            cur.execute('SELECT count(*) FROM cv WHERE profession_name = %s', (item,))
            count = cur.fetchone()
            counts.append(count)
            conn.commit()

        counts = list(sum(counts, ()))

        for item in professions:
            itemUni = translitToURL(item)
            professionsURL.append(itemUni)

        data = list(zip(professions, counts, professionsURL))
    return render_template("cv_cat_pro.html", username=username, data=data, industryURL=industryURL)

# список резюме
@app.route('/cv_cat_list/<username>/<industryURL>/<professionURL>')
def cvCatList(username, industryURL, professionURL):
    userID = getUserID(username)
    industry = translitFromURL(industryURL)
    profession = translitFromURL(professionURL)

    if g.user:
        cur.execute('SELECT cv_id, industry_name, profession_name, min_salary, max_salary, exp, emp_type, cv_pub_data FROM cv WHERE industry_name = %s and profession_name = %s', (industry, profession))
        cvInfo = cur.fetchall()
        conn.commit()
    return render_template("cv_cat_list.html", username=username, cvInfo=cvInfo, userid=userID, industryURL=industryURL, professionURL=professionURL)

# резюме полностью
@app.route('/cv_cat_item/<industryURL>/<professionURL>/<userid>/<itemid>', methods=['GET', 'POST'])
def cvCatItem(userid, itemid, industryURL, professionURL):
    if g.user:
        data = date.today()

        cur.execute("insert into browsing (user_id, cv_id, view_data) values (%s, %s, %s)", (userid, itemid, data))
        conn.commit()

        cur.execute('SELECT * FROM cv WHERE cv_id = %s', (itemid,))
        result = cur.fetchall()
        cvInfo = list(sum(result, ()))
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
    industriesURL = []

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

    for item in industries:
        itemUni = translitToURL(item)
        industriesURL.append(itemUni)

    data = list(zip(industries, counts, industriesURL))
    return render_template("vacancy_cat_ind.html", data=data)

# должности
@app.route('/vacancy_cat_pro/<industryURL>')
def vacCatPro(industryURL):
    counts = []
    professionsURL = []
    industry = translitFromURL(industryURL)

    cur.execute('SELECT profession_name FROM industry_profession WHERE profession_name in (select profession_name from vacancy where industry_name = %s)', (industry,))
    professions = cur.fetchall()
    conn.commit()

    professions = list(sum(professions, ()))

    for item in professions:
        cur.execute('SELECT count(*) FROM vacancy WHERE profession_name = %s', (item,))
        count = cur.fetchone()
        counts.append(count)
        conn.commit()

    counts = list(sum(counts, ()))

    for item in professions:
        itemUni = translitToURL(item)
        professionsURL.append(itemUni)

    data = list(zip(professions, counts, professionsURL))
    return render_template("vacancy_cat_pro.html", data=data, industryURL=industryURL)

# список вакансий
@app.route('/vacancy_cat_list/<industryURL>/<professionURL>')
def vacCatList(industryURL, professionURL):
    industry = translitFromURL(industryURL)
    profession = translitFromURL(professionURL)

    cur.execute('SELECT vacancy_id, industry_name, profession_name, employee_sex, min_emp_age, max_emp_age, min_salary, min_exp, emp_type, vac_pub_data FROM vacancy WHERE industry_name = %s and profession_name = %s', (industry, profession))
    vacancyInfo = cur.fetchall()
    conn.commit()
    return render_template("vacancy_cat_list.html", vacancyInfo=vacancyInfo, industryURL=industryURL, professionURL=professionURL)

# вакансия полностью
@app.route('/vacancy_cat_item/<industryURL>/<professionURL>/<itemid>', methods=['GET', 'POST'])
def vacCatItem(itemid, industryURL, professionURL):
    cur.execute('SELECT vacancy_id, industry_name, profession_name, employee_sex, min_emp_age, max_emp_age, min_salary, min_exp, emp_type, vac_pub_data FROM vacancy WHERE vacancy_id = %s', (itemid))
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

# КАТАЛОГ ЗАДАНИЙ
# сферы деятельности
@app.route('/task_cat_areas/')
def taskCatAreas():
    counts = []
    areasURL = []

    cur.execute('SELECT area_name FROM area WHERE area_name in (select area_name from task) group by area_name')
    areas = cur.fetchall()
    conn.commit()

    areas = list(sum(areas, ()))

    for item in areas:
        cur.execute('SELECT count(*) FROM task WHERE area_name = %s', (item,))
        count = cur.fetchone()
        counts.append(count)
        conn.commit()

    counts = list(sum(counts, ()))

    for item in areas:
        itemUni = translitToURL(item)
        areasURL.append(itemUni)

    data = list(zip(areas, counts, areasURL))
    return render_template("task_cat_areas.html", data=data)

# список заданий
@app.route('/task_cat_list/<areaURL>')
def taskCatList(areaURL):
    area = translitFromURL(areaURL)

    cur.execute('SELECT task_id, area_name, task_descr, exec_date, price FROM task WHERE area_name = %s', (area,))
    taskInfo = cur.fetchall()
    conn.commit()
    return render_template("task_cat_list.html", taskInfo=taskInfo, areaURL=areaURL)

# задание полностью
@app.route('/task_cat_item/<itemid>', methods=['GET', 'POST'])
def taskCatItem(itemid):
    cur.execute('SELECT task_id, area_name, task_descr, exec_date, price FROM task WHERE task_id = %s', (itemid,))
    result = cur.fetchall()
    taskInfo = list(sum(result , ()))
    conn.commit()

    cur.execute('SELECT customer_name FROM customer WHERE user_id = (select user_id from task where task_id = %s)', (itemid,))
    result = cur.fetchone()
    customerName = result[0]
    conn.commit()

    cur.execute('SELECT email, phone FROM person WHERE user_id = (select user_id from task where task_id = %s)', (itemid,))
    result = cur.fetchall()
    contacts = list(sum(result , ()))
    conn.commit()
    return render_template("task_cat_item.html", taskInfo=taskInfo, customerName=customerName, contacts=contacts)

# КАТАЛОГ ИСПОЛНИТЕЛЕЙ
# сферы деятельности
@app.route('/perf_cat_areas/<username>')
def perfCatAreas(username):
    if g.user:
        counts = []

        cur.execute('SELECT area_name FROM area WHERE area_name in (select area_name from performer)')
        areas = cur.fetchall()
        conn.commit()

        areas = list(sum(areas, ()))

        for item in areas:
            cur.execute('SELECT count(*) FROM performer WHERE area_name = %s', (item,))
            count = cur.fetchone()
            counts.append(count)
            conn.commit()

        counts = list(sum(counts, ()))

        data = list(zip(areas, counts))
    return render_template("perf_cat_areas.html", username=username, data=data)

# список исполнителей
@app.route('/perf_cat_list/<username>/<area>')
def perfCatList(username, area):
    cur.execute('SELECT * FROM performer WHERE area_name = %s', (area,))
    perfInfo = cur.fetchall()
    conn.commit()
    return render_template("perf_cat_list.html", username=username, perfInfo=perfInfo, area=area)

# исполнитель полностью
@app.route('/perf_cat_item/<username>/<itemid>')
def perfCatItem(username, itemid):
    cur.execute('SELECT * FROM performer WHERE user_id = %s', (itemid,))
    result = cur.fetchall()
    perfInfo = list(sum(result , ()))
    conn.commit()

    cur.execute('SELECT email, phone FROM person WHERE user_id = (select user_id from performer where user_id = %s)', (itemid,))
    result = cur.fetchall()
    contacts = list(sum(result , ()))
    conn.commit()
    return render_template("perf_cat_item.html", username=username, perfInfo=perfInfo, contacts=contacts)

# удаление сессии
@app.route('/dropsession')
def dropsession():
    session.pop('user', None)
    return redirect(url_for('index'))

# панель администратора
@app.route('/admin')
def admin():
    if g.user:
        return render_template("admin.html")

# АДМИНКА, ОТРАСЛИ И ДОЛЖНОСТИ
# добавление
@app.route('/admin_data_ip_add', methods=['GET', 'POST'])
def adminDataIPAdd():
    if g.user:
        industries = selectColumn('industry_name', 'industry_profession')
        professions = selectColumn('profession_name', 'industry_profession')

        form = IpAddForm()

        if form.validate_on_submit():
            industry = form.industry.data
            profession = form.profession.data

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
                return render_template("admin_data_ip_add.html", message='Данная отрасль или должность уже существует!', industries=industries, professions=professions, form=form)
    return render_template("admin_data_ip_add.html", industries=industries, professions=professions, form=form)

# изменение
@app.route('/admin_data_ind_edit', methods=['GET', 'POST'])
def adminDataIndEdit():
    form = IndEditForm()

    if g.user:
        industries = selectColumn('industry_name', 'industry')

        if form.validate_on_submit():
            industryOld = form.industryOld.data
            industryNew = form.industryNew.data
            try:
                cur.execute("update industry set industry_name = %s WHERE industry_name = %s",
                            (industryNew, industryOld))
                conn.commit()
                return redirect(url_for('adminDataIndEdit'))
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("admin_data_ind_edit.html", message='Данная отрасль уже существует!', form=form)
    return render_template("admin_data_ind_edit.html", industries=industries, form=form)

# АДМИНКА, СФЕРЫ ДЕЯТЕЛЬНОСТИ
# добавление
@app.route('/admin_data_areas_add', methods=['GET', 'POST'])
def adminDataAreasAdd():
    form = AreasAddForm()

    if g.user:
        areas = selectColumn('area_name', 'area')

        if form.validate_on_submit():
            area = form.area.data

            try:
                cur.execute("insert into area (area_name) values (%s)", (area, ))
                conn.commit()
                return redirect(url_for('adminDataAreasAdd'))
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("admin_data_areas_add.html", message='Данная сфера деятельности уже существует!', form=form)
    return render_template("admin_data_areas_add.html", areas=areas, form=form)

# изменение
@app.route('/admin_data_areas_edit', methods=['GET', 'POST'])
def adminDataAreasEdit():
    form = AreasEditForm()

    if g.user:
        areas = selectColumn('area_name', 'area')

        if form.validate_on_submit():
            areaOld = form.areaOld.data
            areaNew = form.areaNew.data

            try:
                cur.execute("update area set area_name = %s WHERE area_name = %s", (areaNew, areaOld))
                conn.commit()
                return redirect(url_for('adminDataAreasEdit'))
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                return render_template("admin_data_areas_edit.html", message='Данная сфера деятельности уже существует!', form=form)
    return render_template("admin_data_areas_edit.html", areas=areas, form=form)

# АДМИНКА, УДАЛЕНИЕ
# удаление резюме
@app.route('/admin_delete_cv', methods=['GET', 'POST'])
def adminDeleteCv():
    form = DateForm()

    if g.user and form.validate_on_submit():
        date = form.date.data

        cur.execute('delete from cv where cv_pub_data::date < %s::date', (date,))
        conn.commit()
        return render_template("admin_delete_cv.html", form=form, message="Данные успешно удалены!")
    return render_template("admin_delete_cv.html", form=form)

# удаление вакансий
@app.route('/admin_delete_vacancy', methods=['GET', 'POST'])
def adminDeleteVacancy():
    form = DateForm()

    if g.user and form.validate_on_submit():
        date = form.date.data

        cur.execute('delete from vacancy where vac_pub_data::date < %s::date', (date,))
        conn.commit()
        return render_template("admin_delete_vacancy.html", form=form, message="Данные успешно удалены!")
    return render_template("admin_delete_vacancy.html", form=form)

# удаление заданий
@app.route('/admin_delete_task', methods=['GET', 'POST'])
def adminDeleteTask():
    form = DateForm()

    if g.user and form.validate_on_submit():
        date = form.date.data

        cur.execute('delete from task where exec_date::date < %s::date', (date,))
        conn.commit()
        return render_template("admin_delete_task.html", form=form, message="Данные успешно удалены!")
    return render_template("admin_delete_task.html", form=form)

if __name__ == '__main__':
    app.run(debug=True)
