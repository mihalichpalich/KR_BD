from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.fields.html5 import EmailField, TelField


class SignUpForm(FlaskForm):
    login = StringField("Логин: ")
    password = PasswordField("Пароль: ")
    status = SelectField("Выберите статус: ", choices=[("Компания", "company"),
                                                       ("Соискатель", "employee"),
                                                       ("Заказчик", "customer"),
                                                       ("Исполнитель", "performer")])
    email = EmailField("Email: ")
    phone = TelField("Телефон: ")