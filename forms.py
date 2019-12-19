from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import InputRequired, Length

class SignUpForm(FlaskForm):
    login = StringField("Логин: ", validators=[InputRequired("Не введен логин!"),
                                               Length(min=4, max=10, message="Логин должен быть длиной от 5 до 10 символов")])
    password = PasswordField("Пароль: ", validators=[InputRequired("Не введен пароль!")])
    status = SelectField("Выберите статус: ", choices=[("company", "Компания"),
                                                       ("employee", "Соискатель"),
                                                       ("customer", "Заказчик"),
                                                       ("performer", "Исполнитель")],
                        validators = [InputRequired("Не выбран статус!")])
    email = EmailField("Email: ", validators=[InputRequired("Не введен email!")])
    phone = TelField("Телефон: ", validators=[InputRequired("Не введен телефон!")])