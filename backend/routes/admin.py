from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..models import Chat, ChatParticipant, ChannelSubscription, Message, User

admin_bp = Blueprint("admin", __name__)
ADMIN_PANEL_PASSWORD = "melonlimelemon"


def _check_admin_password():
    pwd = request.headers.get("X-Admin-Panel-Password") or request.args.get("admin_password")
    return pwd == ADMIN_PANEL_PASSWORD


@admin_bp.get("/settings")
@jwt_required()
def admin_settings():
    if not _check_admin_password():
        return jsonify({"error": "Неверный пароль админ-панели"}), 403

    return jsonify(
        {
            "users_total": User.query.count(),
            "chats_total": Chat.query.count(),
            "messages_total": Message.query.count(),
            "groups_total": Chat.query.filter_by(type="group").count(),
            "channels_total": Chat.query.filter_by(type="channel").count(),
        }
    )


@admin_bp.get("/users")
@jwt_required()
def admin_users():
    if not _check_admin_password():
        return jsonify({"error": "Неверный пароль админ-панели"}), 403

    users = User.query.order_by(User.created_at.desc()).all()
    payload = []
    for u in users:
        participated = ChatParticipant.query.filter_by(user_id=u.id).count()
        subscribed = ChannelSubscription.query.filter_by(user_id=u.id).count()
        payload.append(
            {
                "id": u.id,
                "login": u.login,
                "nickname": u.nickname,
                "status": u.status,
                "is_online": u.is_online,
                "created_at": u.created_at.isoformat(),
                "participated_chats": participated,
                "subscribed_channels": subscribed,
            }
        )

    return jsonify(payload)


@admin_bp.get("/users/<int:user_id>/chats")
@jwt_required()
def admin_user_chats(user_id):
    if not _check_admin_password():
        return jsonify({"error": "Неверный пароль админ-панели"}), 403

    chat_ids = [p.chat_id for p in ChatParticipant.query.filter_by(user_id=user_id).all()]
    chat_ids.extend([s.channel_id for s in ChannelSubscription.query.filter_by(user_id=user_id).all()])

    chats = Chat.query.filter(Chat.id.in_(set(chat_ids))).order_by(Chat.created_at.desc()).all() if chat_ids else []
    return jsonify(
        [
            {
                "id": c.id,
                "type": c.type,
                "title": c.title,
                "description": c.description,
                "owner_id": c.owner_id,
                "created_at": c.created_at.isoformat(),
            }
            for c in chats
        ]
    )
