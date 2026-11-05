import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:123@127.0.0.1:5432/data_analyzer",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = BASE_DIR / "uploads"
    PLOTS_FOLDER = BASE_DIR / "plots"

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # максимум 50 МБ на файл
    ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
