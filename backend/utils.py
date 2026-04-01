import os
import uuid
from pathlib import Path

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


def stickers_root() -> Path:
    return Path(current_app.root_path) / "stickers"


def list_sticker_packs():
    root = stickers_root()
    if not root.exists():
        return []

    packs = []
    for folder in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name.lower()):
        cover = root / f"{folder.name}.png"
        stickers = sorted([s for s in folder.glob("*.png") if s.is_file()], key=lambda p: p.name.lower())
        packs.append({
            "name": folder.name,
            "cover_url": f"/stickers/{cover.name}" if cover.exists() else None,
            "stickers": [
                {
                    "name": sticker.stem,
                    "path": f"{folder.name}/{sticker.name}",
                    "url": f"/stickers/{folder.name}/{sticker.name}",
                }
                for sticker in stickers
            ],
        })
    return packs


def is_allowed_sticker_path(sticker_path: str) -> bool:
    sanitized = sticker_path.replace("\\", "/").strip("/")
    full = stickers_root() / sanitized
    root = stickers_root().resolve()
    try:
        resolved = full.resolve()
    except FileNotFoundError:
        return False
    return resolved.is_file() and resolved.suffix.lower() == ".png" and str(resolved).startswith(str(root))


def build_message_payload(message):
    reply_to = None
    if message.reply_to and not message.reply_to.deleted:
        reply_to = {
            "id": message.reply_to.id,
            "sender_id": message.reply_to.sender_id,
            "text": message.reply_to.text,
            "file_type": message.reply_to.file_type,
            "file_url": message.reply_to.file_url,
        }

    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "text": message.text,
        "file_url": message.file_url,
        "file_type": message.file_type,
        "file_name": message.file_name,
        "file_size": message.file_size,
        "reply_to_id": message.reply_to_id,
        "reply_to": reply_to,
        "created_at": message.created_at.isoformat(),
        "reactions": [{"user_id": r.user_id, "type": r.reaction_type} for r in message.reactions],
    }
