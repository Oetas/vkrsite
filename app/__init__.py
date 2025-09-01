import os
from flask import Flask
from .extensions import db, migrate, login_manager
from .main import main_bp

def create_app():
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object("config.Config")

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"  # позже добавим страницу логина

    # blueprints
    app.register_blueprint(main_bp)

    # simple health route (проверка)
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
