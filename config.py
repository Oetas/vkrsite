# config.py — конфигурация проекта

import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure")

    # Подключение к PostgreSQL
    DB_USER = os.getenv("POSTGRES_USER", "postgres")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
    DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
    DB_PORT = os.getenv("POSTGRES_PORT", "5432")
    DB_NAME = os.getenv("POSTGRES_DB", "vkrsite")

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Папка для загрузок (от корня проекта)
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

    # Максимум 16 MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Разрешённые расширения
    ALLOWED_UPLOAD_EXTENSIONS = {"pdf", "docx", "xlsx"}
