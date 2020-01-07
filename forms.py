from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, RadioField
from wtforms.validators import InputRequired, Length

class SignUpForm(FlaskForm):
    login = StringField('Логин', validators=[InputRequired('Не введен логин'), Length(max=15, message='Логин не должен превышать 15 символов')])
    password = PasswordField('Пароль', validators=[InputRequired('Не введен пароль')])
    email = StringField('Email', validators=[InputRequired("Не введен email")])
    phone = StringField('Телефон', validators=[InputRequired('Не введен телефон')])
    status = RadioField('Выберите статус: ', choices=[('company', 'Работодатель'), ('employee', 'Соискатель'), ('customer', 'Заказчик'), ('performer', 'Исполнитель')])

class LoginForm(FlaskForm):
    login = StringField('Логин', validators=[InputRequired('Не введен логин')])
    password = PasswordField('Пароль', validators=[InputRequired('Не введен пароль')])