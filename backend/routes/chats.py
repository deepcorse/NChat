from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import and_, or_

from ..models import Chat, ChatParticipant, ChannelSubscription, Message, User, db
from ..utils import save_upload

chats_bp = Blueprint("chats", __name__)


def _is_participant(user_id, chat_id):
    chat = Chat.query.get_or_404(chat_id)
    if chat.type == "channel":
        if chat.owner_id == user_id:
            return True
        return ChannelSubscription.query.filter_by(user_id=user_id, channel_id=chat_id).first() is not None
    return ChatParticipant.query.filter_by(user_id=user_id, chat_id=chat_id).first() is not None


@chats_bp.get("")
@jwt_required()
def list_chats():
    user_id = int(get_jwt_identity())
    participant_chat_ids = db.session.query(ChatParticipant.chat_id).filter(ChatParticipant.user_id == user_id)
    sub_chat_ids = db.session.query(ChannelSubscription.channel_id).filter(ChannelSubscription.user_id == user_id)

    chats = Chat.query.filter(
        or_(Chat.id.in_(participant_chat_ids), Chat.id.in_(sub_chat_ids), Chat.owner_id == user_id)
    ).order_by(Chat.created_at.desc()).all()

    response = []
    for chat in chats:
        last = Message.query.filter_by(chat_id=chat.id, deleted=False).order_by(Message.created_at.desc()).first()
        response.append({
            "id": chat.id,
            "type": chat.type,
            "title": chat.title,
            "avatar": chat.avatar,
            "description": chat.description,
            "last_message": last.text if last else None,
            "last_message_at": last.created_at.isoformat() if last else None,
        })
    return jsonify(response)


@chats_bp.post("/private")
@jwt_required()
def create_private_chat():
    user_id = int(get_jwt_identity())
    other_user_id = (request.get_json() or {}).get("user_id")
    if not other_user_id or other_user_id == user_id:
        return jsonify({"error": "Некорректный пользователь"}), 400

    existing = (
        db.session.query(Chat)
        .join(ChatParticipant, Chat.id == ChatParticipant.chat_id)
        .filter(Chat.type == "private")
        .group_by(Chat.id)
        .having(db.func.count(ChatParticipant.id) == 2)
        .all()
    )

    for chat in existing:
        ids = {p.user_id for p in chat.participants}
        if ids == {user_id, other_user_id}:
            return jsonify({"chat_id": chat.id, "message": "Чат уже существует"})

    chat = Chat(type="private", title="private")
    db.session.add(chat)
    db.session.flush()
    db.session.add(ChatParticipant(user_id=user_id, chat_id=chat.id, role="member"))
    db.session.add(ChatParticipant(user_id=other_user_id, chat_id=chat.id, role="member"))
    db.session.commit()
    return jsonify({"chat_id": chat.id}), 201


@chats_bp.get("/<int:chat_id>/messages")
@jwt_required()
def chat_messages(chat_id):
    user_id = int(get_jwt_identity())
    if not _is_participant(user_id, chat_id):
        return jsonify({"error": "Нет доступа"}), 403

    limit = min(int(request.args.get("limit", 30)), 100)
    before_id = request.args.get("before_id", type=int)

    query = Message.query.filter_by(chat_id=chat_id, deleted=False)
    if before_id:
        query = query.filter(Message.id < before_id)

    items = query.order_by(Message.id.desc()).limit(limit).all()
    return jsonify([
        {
            "id": m.id,
            "chat_id": m.chat_id,
            "sender_id": m.sender_id,
            "text": m.text,
            "file_url": m.file_url,
            "file_type": m.file_type,
            "file_name": m.file_name,
            "file_size": m.file_size,
            "created_at": m.created_at.isoformat(),
            "reactions": [{"user_id": r.user_id, "type": r.reaction_type} for r in m.reactions],
        }
        for m in reversed(items)
    ])


@chats_bp.post("/<int:chat_id>/messages")
@jwt_required()
def send_message(chat_id):
    user_id = int(get_jwt_identity())
    chat = Chat.query.get_or_404(chat_id)
    if not _is_participant(user_id, chat_id):
        return jsonify({"error": "Нет доступа"}), 403
    if chat.type == "channel" and chat.owner_id != user_id:
        return jsonify({"error": "Только владелец может писать в канал"}), 403

    text = (request.form.get("text") or "").strip()
    file = request.files.get("file")
    file_data = None
    if file:
        try:
            file_data = save_upload(file, "messages")
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    if not text and not file_data:
        return jsonify({"error": "Пустое сообщение"}), 400

    msg = Message(
        chat_id=chat_id,
        sender_id=user_id,
        text=text,
        file_url=file_data["url"] if file_data else None,
        file_type=file_data["file_type"] if file_data else None,
        file_name=file_data["file_name"] if file_data else None,
        file_size=file_data["file_size"] if file_data else None,
    )
    db.session.add(msg)
    db.session.commit()
    current_app.socketio.emit(
        "new_message",
        {"id": msg.id, "chat_id": chat_id, "sender_id": user_id, "text": msg.text, "file_url": msg.file_url},
        room=f"chat_{chat_id}",
    )
    return jsonify({"id": msg.id, "chat_id": chat_id, "text": msg.text, "created_at": msg.created_at.isoformat()}), 201
