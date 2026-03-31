from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Chat, ChatParticipant, Message, db

messages_bp = Blueprint("messages", __name__)


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
