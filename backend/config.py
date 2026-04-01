import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SECRET_KEY = os.getenv("NCHAT_SECRET_KEY", "dev-secret-change-me")
    JWT_SECRET_KEY = os.getenv("NCHAT_JWT_SECRET", "dev-jwt-secret-change-me")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'nchat.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    MAX_CONTENT_LENGTH = 20 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    ALLOWED_EXTENSIONS = {
        "png", "jpg", "jpeg", "gif", "webp", "mp4", "mov", "avi", "mkv", "pdf", "txt", "zip", "rar", "doc", "docx"
    }
