# app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db, login_manager
from .models import User, Role
from .forms import RegisterForm, LoginForm

auth_bp = Blueprint("auth", __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter_by(email=form.email.data).first()
        if existing:
            flash("❌ Email уже используется")
            return redirect(url_for("auth.register"))

        hashed_pw = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data, password_hash=hashed_pw)

        # По умолчанию студент
        role = Role.query.filter_by(name="student").first()
        if role:
            user.roles.append(role)

        db.session.add(user)
        db.session.commit()
        flash("✅ Регистрация успешна. Войдите в систему.")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("✅ Успешный вход")
            return redirect(url_for("index"))
        flash("❌ Неверный логин или пароль")
    return render_template("login.html", form=form)

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("👋 Вы вышли из системы")
    return redirect(url_for("index"))
