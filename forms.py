from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, DateField, SelectField
from wtforms.validators import InputRequired, Length, DataRequired

from functions import *

class SignUpForm(FlaskForm):
    login = StringField('Логин', validators=[InputRequired('Не введен логин'), Length(max=15, message='Логин не должен превышать 15 символов')])
    password = PasswordField('Пароль', validators=[InputRequired('Не введен пароль')])
    email = StringField('Email', validators=[InputRequired("Не введен email")])
    phone = StringField('Телефон', validators=[InputRequired('Не введен телефон')])
    status = RadioField('Выберите статус: ', choices=[('company', 'Работодатель'), ('employee', 'Соискатель'), ('customer', 'Заказчик'), ('performer', 'Исполнитель')])

class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[InputRequired('Не введен логин')])
    password = PasswordField('Пароль', validators=[InputRequired('Не введен пароль')])

class PwRecForm(FlaskForm):
    login = StringField('Введите логин: ', validators=[InputRequired('Не введен логин')])
    passwordOld = PasswordField('Введите новый пароль: ', validators=[InputRequired('Не введен пароль')])
    passwordNew = PasswordField('Введите новый пароль еще раз: ', validators=[InputRequired('Не введен пароль')])

class IpAddForm(FlaskForm):
    industry = StringField('Введите отрасль: ', validators=[InputRequired('Не введена отрасль')])
    profession = StringField('Введите соответствующую ей должность: ', validators=[InputRequired('Не введена должность')])

class IndEditForm(FlaskForm):
    industryOld = StringField('Введите название отрасли: ', validators=[InputRequired('Не введена отрасль')])
    industryNew = StringField('Введите новое название отрасли: ', validators=[InputRequired('Не введена отрасль')])

class AreasAddForm(FlaskForm):
    area = StringField('Введите сферу деятельности: ', validators=[InputRequired('Не введена сфера деятельности')])

class AreasEditForm(FlaskForm):
    areaOld = StringField('Введите сферу деятельности: ', validators=[InputRequired('Не введена сфера деятельности')])
    areaNew = StringField('Введите новое название: ', validators=[InputRequired('Не введена сфера деятельности')])

class DateForm(FlaskForm):
    date = DateField('', format='%Y-%m-%d', validators=[DataRequired('Дата введена в неправильном формате!')])

class ProfEdCompanyForm(FlaskForm):
    inn = StringField('ИНН: ')
    companyName = StringField('Название фирмы: ')
    companyPhone = StringField('Телефон фирмы: ')
    companyEmail = StringField('e-mail фирмы: ')

class ProfEdEmployeeForm(FlaskForm):
    fullName = StringField('ФИО: ')
    employeePhone = StringField('Телефон: ')
    employeeEmail = StringField('e-mail: ')

class ProfEdCustomerForm(FlaskForm):
    customerName = StringField('Имя: ')
    customerPhone = StringField('Телефон: ')
    customerEmail = StringField('e-mail: ')

class ProfEdPerformerForm(FlaskForm):
    areasSelect = []

    areas = selectColumn('area_name', 'area')
    for i in areas:
        areasSelect.append((i, i))
    areasSelect.append(('', ''))

    performerName = StringField('Имя: ')
    performerArea = SelectField('Выберите сферу деятельности: ', choices=areasSelect)
    servicesDescr = StringField('О своей деятельности:  ')
    performerPhone = StringField('Телефон: ')
    performerEmail = StringField('e-mail: ')