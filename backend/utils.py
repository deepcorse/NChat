import os
import uuid
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename: str) -> bool:
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in current_app.config["ALLOWED_EXTENSIONS"]


def classify_file(filename: str) -> str:
    ext = filename.rsplit(".", 1)[1].lower() if "." in filename else ""
    if ext in {"png", "jpg", "jpeg", "gif", "webp"}:
        return "image"
    if ext in {"mp4", "mov", "avi", "mkv"}:
        return "video"
    return "file"


def save_upload(file_storage, subfolder="files"):
    if not file_storage or file_storage.filename == "":
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("Недопустимый тип файла")

    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(folder, exist_ok=True)

    original = secure_filename(file_storage.filename)
    ext = original.rsplit(".", 1)[1].lower() if "." in original else "bin"
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(folder, unique_name)
    file_storage.save(path)

    return {
        "url": f"/uploads/{subfolder}/{unique_name}",
        "file_name": original,
        "file_size": os.path.getsize(path),
        "file_type": classify_file(original),
    }
