import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .auth import auth_bp
from app.utils import roles_required
from flask_login import login_required
from .main import main_bp
from .admin import admin_bp


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    app.config.from_object("config.Config")

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # указываем с префиксом blueprint

    # импорт моделей (чтобы Alembic их видел)
    from app import models  # noqa

    # регистрация блюпринтов
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)          # публичные пути в корне
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # регистрируем фильтр nl2br
    @app.template_filter("nl2br")
    def nl2br_filter(s):
        return s.replace("\n", "<br>\n")

    # тестовые роуты
    @app.route("/")
    def index():
        return "Привет! Это главная страница."

    @app.route("/admin")
    @login_required
    @roles_required("admin")
    def admin_panel():
        return "Добро пожаловать в админку!"

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
