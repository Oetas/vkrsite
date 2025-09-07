# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileField, FileRequired, FileAllowed

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

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

