from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Chat, ChatParticipant, ChannelSubscription, Message, db
from ..utils import build_message_payload

messages_bp = Blueprint("messages", __name__)


def _has_access(user_id, chat):
    if chat.type == "channel":
        if chat.owner_id == user_id:
            return True
        return ChannelSubscription.query.filter_by(user_id=user_id, channel_id=chat.id).first() is not None
    return ChatParticipant.query.filter_by(chat_id=chat.id, user_id=user_id).first() is not None


@messages_bp.delete("/<int:message_id>")
@jwt_required()
def delete_message(message_id):
    user_id = int(get_jwt_identity())
    msg = Message.query.get_or_404(message_id)
    chat = Chat.query.get_or_404(msg.chat_id)

    can_delete = msg.sender_id == user_id
    if chat.type == "group":
        part = ChatParticipant.query.filter_by(chat_id=chat.id, user_id=user_id, role="admin").first()
        can_delete = can_delete or part is not None
    if chat.type == "channel":
        can_delete = can_delete or chat.owner_id == user_id

    if not can_delete:
        return jsonify({"error": "Недостаточно прав"}), 403

    msg.deleted = True
    db.session.commit()
    current_app.socketio.emit("message_deleted", {"message_id": msg.id, "chat_id": msg.chat_id}, room=f"chat_{msg.chat_id}")
    return jsonify({"message": "Сообщение удалено"})


@messages_bp.post("/<int:message_id>/forward")
@jwt_required()
def forward_message(message_id):
    user_id = int(get_jwt_identity())
    source_message = Message.query.get_or_404(message_id)
    source_chat = Chat.query.get_or_404(source_message.chat_id)

    if not _has_access(user_id, source_chat):
        return jsonify({"error": "Нет доступа к исходному чату"}), 403

    payload = request.get_json() or {}
    target_chat_id = payload.get("target_chat_id")
    if not target_chat_id:
        return jsonify({"error": "Не указан target_chat_id"}), 400

    target_chat = Chat.query.get_or_404(target_chat_id)
    if not _has_access(user_id, target_chat):
        return jsonify({"error": "Нет доступа к целевому чату"}), 403
    if target_chat.type == "channel" and target_chat.owner_id != user_id:
        return jsonify({"error": "В канал может пересылать только владелец"}), 403

    forwarded_title = source_chat.title or ("Личный чат" if source_chat.type == "private" else "Чат")
    new_message = Message(
        chat_id=target_chat.id,
        sender_id=user_id,
        text=source_message.text,
        file_url=source_message.file_url,
        file_type=source_message.file_type,
        file_name=source_message.file_name,
        file_size=source_message.file_size,
        forwarded_from_chat_id=source_chat.id,
        forwarded_from_message_id=source_message.id,
        forwarded_from_title=forwarded_title,
    )
    db.session.add(new_message)
    db.session.commit()

    data = build_message_payload(new_message, viewer_id=user_id)
    current_app.socketio.emit("new_message", data, room=f"chat_{target_chat.id}")
    return jsonify(data), 201
