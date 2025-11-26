# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import SelectField, BooleanField
from wtforms import SelectMultipleField

class RegisterForm(FlaskForm):
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Повторите пароль", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Зарегистрироваться")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")

class ContactForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired(), Length(max=255)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    subject = StringField("Тема", validators=[Length(max=255)])
    message = TextAreaField("Сообщение", validators=[DataRequired(), Length(min=5)])
    submit = SubmitField("Отправить")

class FileUploadForm(FlaskForm):
    file = FileField("Файл (PDF/DOCX/XLSX)", validators=[
        FileRequired(),
        FileAllowed(["pdf", "docx", "xlsx"], "Только pdf/docx/xlsx")
    ])
    submit = SubmitField("Загрузить")

class AdminUserForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    username = StringField("Имя пользователя", validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField("Пароль", validators=[DataRequired(), Length(min=6)])

    roles = SelectMultipleField("Роли", coerce=int)

class CourseForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=255)])
    slug = StringField("Slug", validators=[DataRequired(), Length(max=255)])
    description = TextAreaField("Description")
    level = SelectField("Level", choices=[("beginner","beginner"),("intermediate","intermediate"),("advanced","advanced")])
    is_published = BooleanField("Published")
    submit = SubmitField("Save")

