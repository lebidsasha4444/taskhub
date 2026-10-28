import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    DEBUG = os.getenv("DEBUG", "false").strip().lower() in {"1", "true", "yes", "on"}
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///taskhub.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
