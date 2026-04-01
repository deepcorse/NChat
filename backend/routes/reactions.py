from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Message, Reaction, db

reactions_bp = Blueprint("reactions", __name__)

ALLOWED_REACTIONS = ["👍", "❤️", "😂", "😮", "😢", "😡", "🎉", "🤔", "👎", "🔥", "🚀", "👀", "💯", "✅", "🆒"]


@reactions_bp.post("/<int:message_id>/reactions")
@jwt_required()
def toggle_reaction(message_id):
    user_id = int(get_jwt_identity())
    msg = Message.query.get_or_404(message_id)
    reaction_type = (request.get_json() or {}).get("reaction_type")
    if reaction_type not in ALLOWED_REACTIONS:
        return jsonify({"error": "Недопустимая реакция"}), 400

    existing = Reaction.query.filter_by(message_id=msg.id, user_id=user_id, reaction_type=reaction_type).first()
    if existing:
        db.session.delete(existing)
        db.session.commit()
        status = "removed"
    else:
        db.session.add(Reaction(message_id=msg.id, user_id=user_id, reaction_type=reaction_type))
        db.session.commit()
        status = "added"

    grouped = {}
    for r in Reaction.query.filter_by(message_id=msg.id).all():
        grouped[r.reaction_type] = grouped.get(r.reaction_type, 0) + 1

    current_app.socketio.emit(
        "reaction_updated",
        {"message_id": msg.id, "chat_id": msg.chat_id, "reactions": grouped},
        room=f"chat_{msg.chat_id}",
    )
    return jsonify({"status": status, "reactions": grouped})
