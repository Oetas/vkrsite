import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .dashboard import dashboard_bp

def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    app.config.from_object("config.Config")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    # Ensure uploads folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # указываем с префиксом blueprint

    # импорт моделей (чтобы Alembic их видел)
    from app import models  # noqa

    # Импорт блюпринтов локально — для избежания циклических импортов
    from .auth import auth_bp
    from .main import main_bp
    from .admin import admin_bp

    # регистрация блюпринтов
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)          # публичные пути в корне
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # регистрируем фильтр nl2br
    @app.template_filter("nl2br")
    def nl2br_filter(s):
        return s.replace("\n", "<br>\n")

    # тестовые роуты (по желанию — можно удалить)
    @app.route("/")
    def index():
        return "Привет! Это главная страница."

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
