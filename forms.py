from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField, DateField, SelectField, IntegerField
from wtforms.validators import InputRequired, Length, DataRequired, Optional, Email, Regexp

from functions import *

industriesSelect = []
professionsSelect = []
areasSelect = []

industries = selectColumn('industry_name', 'industry')
professions = selectColumn('profession_name', 'profession')
areas = selectColumn('area_name', 'area')

for i in industries:
    industriesSelect.append((i, i))
for i in professions:
    professionsSelect.append((i, i))
for i in areas:
    areasSelect.append((i, i))

class SignUpForm(FlaskForm):
    login = StringField('Логин', validators=[InputRequired('Не введен логин'), Length(max=15, message='Логин не должен превышать 15 символов'), Regexp('^[a-zA-Z0-9_]+$', message="Логин должен содержать только латинские буквы, цифры и _")])
    password = PasswordField('Пароль', validators=[InputRequired('Не введен пароль'), Regexp('^[a-zA-Z0-9_]+$', message="Пароль должен содержать только латинские буквы, цифры и _")])
    email = StringField('Email', validators=[InputRequired("Не введен email"), Email("Не похоже на email")])
    phone = StringField('Телефон', validators=[InputRequired('Не введен телефон'), Regexp('^[+()0-9\s]+$', message="Не похоже на email")])
    status = RadioField('Выберите статус: ', choices=[('company', 'Работодатель'), ('employee', 'Соискатель'), ('customer', 'Заказчик'), ('performer', 'Исполнитель')])

class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[InputRequired('Не введен логин')])
    password = PasswordField('Пароль', validators=[InputRequired('Не введен пароль')])

class PwRecForm(FlaskForm):
    login = StringField('Введите логин: ', validators=[InputRequired('Не введен логин')])
    passwordOld = PasswordField('Введите новый пароль: ', validators=[InputRequired('Не введен пароль')])
    passwordNew = PasswordField('Введите новый пароль еще раз: ', validators=[InputRequired('Не введен пароль')])

class IpAddForm(FlaskForm):
    industry = StringField('Введите отрасль: ', validators=[InputRequired('Не введена отрасль'), Regexp('^[а-яА-ЯёЁ\s]+$', message="Вводите русскими символами")])
    profession = StringField('Введите соответствующую ей должность: ', validators=[InputRequired('Не введена должность'), Regexp('^[а-яА-ЯёЁ\s]+$', message="Вводите русскими символами")])

class IndEditForm(FlaskForm):
    industryOld = StringField('Введите название отрасли: ', validators=[InputRequired('Не введена отрасль'), Regexp('^[а-яА-ЯёЁ\s]+$', message="Вводите русскими символами")])
    industryNew = StringField('Введите новое название отрасли: ', validators=[InputRequired('Не введена отрасль'), Regexp('^[а-яА-ЯёЁ\s]+$', message="Вводите русскими символами")])

class AreasAddForm(FlaskForm):
    area = StringField('Введите сферу деятельности: ', validators=[InputRequired('Не введена сфера деятельности'), Regexp('^[а-яА-ЯёЁ\s]+$', message="Вводите русскими символами")])

class AreasEditForm(FlaskForm):
    areaOld = StringField('Введите сферу деятельности: ', validators=[InputRequired('Не введена сфера деятельности'), Regexp('^[а-яА-ЯёЁ\s]+$', message="Вводите русскими символами")])
    areaNew = StringField('Введите новое название: ', validators=[InputRequired('Не введена сфера деятельности'), Regexp('^[а-яА-ЯёЁ\s]+$', message="Вводите русскими символами")])

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
    performerName = StringField('Имя: ')
    performerArea = SelectField('Выберите сферу деятельности: ', choices=areasSelect)
    servicesDescr = StringField('О своей деятельности:  ')
    performerPhone = StringField('Телефон: ')
    performerEmail = StringField('e-mail: ')

class CreateItemCompanyForm(FlaskForm):
    industryName = SelectField('Выберите отрасль*: ', choices=industriesSelect)
    professionName = SelectField('Выберите должность*: ', choices=professionsSelect)
    employeeSex = SelectField('Выберите пол соискателя: ', choices=[('', ''), ('мужской', 'мужской'), ('женский', 'женский')], default='')
    minEmpAge = StringField('Минимальный возраст соискателя, лет (числом)*: ', validators=[InputRequired('Не введен минимальный возраст соискателя')])
    maxEmpAge = StringField('Максимальный возраст соискателя, лет (числом): ')
    minSalary = StringField('Минимальная заработная плата, руб (числом)*: ', validators=[InputRequired('Не введена минимальная заработная плата')])
    minExp = IntegerField('Минимальный опыт работы, лет (числом, если без опыта, то 0)*: ', validators=[Optional(strip_whitespace=False)])
    empType = SelectField('Выберите тип занятости: ', choices=[('полная', 'полная'), ('частичная', 'частичная'), ('вахта', 'вахта'), ('удаленная работа', 'удаленная работа'), ('стажировка', 'стажировка')])

class CreateItemEmployeeForm(FlaskForm):
    industryName = SelectField('Выберите отрасль*: ', choices=industriesSelect)
    professionName = SelectField('Выберите должность*: ', choices=professionsSelect)
    minSalary = StringField('Минимальная заработная плата, руб (числом): ')
    maxSalary = StringField('Максимальная заработная плата, руб (числом): ')
    exp = IntegerField('Опыт работы, лет (числом, если без опыта, то 0)*: ', validators=[Optional(strip_whitespace=False), InputRequired('Не введен опыт работы')])
    empType = SelectField('Выберите тип занятости: ',
                          choices=[('полная', 'полная'), ('частичная', 'частичная'), ('вахта', 'вахта'),
                                   ('удаленная работа', 'удаленная работа'), ('стажировка', 'стажировка')])

class CreateItemCustomerForm(FlaskForm):
    areaName = SelectField('Выберите сферу деятельности*: ', choices=areasSelect)
    taskDescr = StringField('Опишите задание*: ', validators=[InputRequired('Не введено описание задания')])
    dateInput = DateField('Введите дату выполнения в формате ГГГГ-ММ-ДД*: ', format='%Y-%m-%d', validators=[DataRequired('Дата введена в неправильном формате!')])
    price = IntegerField('Стоимость выполнения (числом, в рублях)*: ', validators=[Optional(strip_whitespace=False), InputRequired('Не введена стоимость выполнения')])
