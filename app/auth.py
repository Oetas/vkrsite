# app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from .extensions import db, login_manager
from .models import User, Role
from .forms import RegisterForm, LoginForm
from flask import request


auth_bp = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    # id у нас BigInteger, но приводить к int нормально
    return User.query.get(int(user_id))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # проверка уникальности email/username
        if User.query.filter_by(email=form.email.data).first():
            flash("❌ Email уже используется")
            return redirect(url_for("auth.register"))
        if User.query.filter_by(username=form.username.data).first():
            flash("❌ Имя пользователя уже занято")
            return redirect(url_for("auth.register"))

        # создаём юзера и хэшируем пароль методом модели
        new_user = User(username=form.username.data, email=form.email.data)
        new_user.set_password(form.password.data)

        # роль по умолчанию = student (через связь many-to-many)
        role = Role.query.filter_by(name="student").first()
        if role is None:
            role = Role(name="student")
            db.session.add(role)  # создадим, если забыли засеять
        new_user.roles.append(role)

        db.session.add(new_user)
        db.session.commit()
        flash("✅ Регистрация успешна. Войдите в систему.")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash("✅ Успешный вход", "success")
            next_page = request.args.get('next')
            # простая проверка: если next есть — редиректим на него, иначе — на index/main
            return redirect(next_page or url_for("main.index"))
        flash("❌ Неверный логин или пароль", "danger")
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("👋 Вы вышли из системы")
    return redirect(url_for("index"))
