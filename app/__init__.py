import os
from flask import Flask
from .extensions import db, migrate, login_manager


def create_app():
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static"
    )
    app.config.from_object("config.Config")

    # Ensure uploads folder exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # импорт моделей
    from app import models  # noqa

    # Блюпринты
    from app.dashboard import dashboard_bp
    from .auth import auth_bp
    from .main import main_bp
    from .admin import admin_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # фильтр nl2br
    @app.template_filter("nl2br")
    def nl2br_filter(s):
        return s.replace("\n", "<br>\n")

    @app.route("/")
    def index():
        return "Привет! Это главная страница."

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
