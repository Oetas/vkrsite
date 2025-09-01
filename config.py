# конфиг (БД и др.)

import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False


'''
DB_URI = "postgresql+psycopg2://username:password@localhost:5432/ml_site"
'''