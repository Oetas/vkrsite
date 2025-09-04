import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .auth import auth_bp

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

    # тестовые роуты
    @app.route("/")
    def index():
        return "Привет! Это главная страница."

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
