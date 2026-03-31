from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_

from ..models import Chat, ChannelSubscription, User, db
from ..utils import save_upload

users_bp = Blueprint("users", __name__)


@users_bp.get("/search")
@jwt_required()
def search_users_and_channels():
    q = (request.args.get("q") or "").strip()
    if len(q) < 1:
        return jsonify([])

    users = User.query.filter(or_(User.login.ilike(f"%{q}%"), User.nickname.ilike(f"%{q}%"))).limit(20).all()
    channels = Chat.query.filter(
        Chat.type == "channel",
        or_(Chat.title.ilike(f"%{q}%"), Chat.description.ilike(f"%{q}%")),
    ).limit(20).all()

    result = [
        {"kind": "user", "id": u.id, "login": u.login, "nickname": u.nickname, "avatar": u.avatar_url}
        for u in users
    ] + [
        {"kind": "channel", "id": c.id, "title": c.title, "description": c.description, "avatar": c.avatar}
        for c in channels
    ]
    return jsonify(result)


@users_bp.get("/<int:user_id>")
@jwt_required()
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({
        "id": user.id,
        "login": user.login,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "status": user.status,
        "description": user.description,
        "is_online": user.is_online,
    })


@users_bp.patch("/me")
@jwt_required()
def patch_me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    data = request.get_json() or {}
    if "nickname" in data:
        user.nickname = (data.get("nickname") or user.nickname).strip() or user.nickname
    if "status" in data:
        user.status = (data.get("status") or "").strip()[:255]
    if "description" in data:
        user.description = (data.get("description") or "").strip()[:255]
    db.session.commit()
    return jsonify({"message": "Профиль обновлён"})


@users_bp.post("/me/avatar")
@jwt_required()
def upload_avatar():
    user = User.query.get_or_404(int(get_jwt_identity()))
    file = request.files.get("avatar")
    if not file:
        return jsonify({"error": "Файл не передан"}), 400
    try:
        saved = save_upload(file, "avatars")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    user.avatar_url = saved["url"]
    db.session.commit()
    return jsonify({"avatar_url": user.avatar_url})
