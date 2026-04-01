from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Chat, ChatParticipant, ChannelSubscription, Message, Poll, PollOption, PollVote, db
from ..utils import build_message_payload, serialize_poll

polls_bp = Blueprint("polls", __name__)


def _has_access(user_id, chat):
    if chat.type == "channel":
        if chat.owner_id == user_id:
            return True
        return ChannelSubscription.query.filter_by(user_id=user_id, channel_id=chat.id).first() is not None
    return ChatParticipant.query.filter_by(chat_id=chat.id, user_id=user_id).first() is not None


@polls_bp.post("/chats/<int:chat_id>/polls")
@jwt_required()
def create_poll(chat_id):
    user_id = int(get_jwt_identity())
    chat = Chat.query.get_or_404(chat_id)
    if not _has_access(user_id, chat):
        return jsonify({"error": "Нет доступа"}), 403
    if chat.type == "channel" and chat.owner_id != user_id:
        return jsonify({"error": "В канале создавать опрос может только владелец"}), 403

    data = request.get_json() or {}
    question = (data.get("question") or "").strip()
    options = [str(x).strip() for x in (data.get("options") or []) if str(x).strip()]
    anonymous = bool(data.get("anonymous", True))
    multiple_choice = bool(data.get("multiple_choice", False))
    quiz_mode = bool(data.get("quiz_mode", False))

    if not question or len(options) < 2:
        return jsonify({"error": "Нужен вопрос и минимум 2 варианта"}), 400
    if len(options) > 10:
        return jsonify({"error": "Максимум 10 вариантов"}), 400

    msg = Message(chat_id=chat_id, sender_id=user_id, text=f"📊 {question}", file_type="poll")
    db.session.add(msg)
    db.session.flush()

    poll = Poll(
        message_id=msg.id,
        chat_id=chat_id,
        creator_id=user_id,
        question=question,
        anonymous=anonymous,
        multiple_choice=multiple_choice,
        quiz_mode=quiz_mode,
    )
    db.session.add(poll)
    db.session.flush()

    option_rows = []
    for opt in options:
        row = PollOption(poll_id=poll.id, text=opt)
        db.session.add(row)
        option_rows.append(row)

    db.session.flush()
    if quiz_mode:
        correct_option_idx = data.get("correct_option_index")
        if isinstance(correct_option_idx, int) and 0 <= correct_option_idx < len(option_rows):
            poll.correct_option_id = option_rows[correct_option_idx].id

    db.session.commit()

    message_payload = build_message_payload(msg, viewer_id=user_id)
    current_app.socketio.emit("new_message", message_payload, room=f"chat_{chat_id}")
    return jsonify(message_payload), 201


@polls_bp.get("/polls/<int:poll_id>")
@jwt_required()
def get_poll(poll_id):
    user_id = int(get_jwt_identity())
    poll = Poll.query.get_or_404(poll_id)
    chat = Chat.query.get_or_404(poll.chat_id)
    if not _has_access(user_id, chat):
        return jsonify({"error": "Нет доступа"}), 403
    return jsonify(serialize_poll(poll, viewer_id=user_id))


@polls_bp.post("/polls/<int:poll_id>/vote")
@jwt_required()
def vote_poll(poll_id):
    user_id = int(get_jwt_identity())
    poll = Poll.query.get_or_404(poll_id)
    chat = Chat.query.get_or_404(poll.chat_id)
    if not _has_access(user_id, chat):
        return jsonify({"error": "Нет доступа"}), 403
    if poll.is_closed:
        return jsonify({"error": "Опрос закрыт"}), 400

    data = request.get_json() or {}
    option_ids = data.get("option_ids") or []
    if isinstance(option_ids, int):
        option_ids = [option_ids]
    option_ids = [int(x) for x in option_ids]
    if not option_ids:
        return jsonify({"error": "Не выбраны варианты"}), 400
    if not poll.multiple_choice and len(option_ids) > 1:
        return jsonify({"error": "Разрешён только один вариант"}), 400

    poll_option_ids = {o.id for o in poll.options}
    if any(x not in poll_option_ids for x in option_ids):
        return jsonify({"error": "Некорректный вариант ответа"}), 400

    PollVote.query.filter_by(poll_id=poll.id, user_id=user_id).delete()
    for opt_id in set(option_ids):
        db.session.add(PollVote(poll_id=poll.id, option_id=opt_id, user_id=user_id))
    db.session.commit()

    current_app.socketio.emit("poll_updated", {"poll_id": poll.id}, room=f"chat_{poll.chat_id}")
    return jsonify(serialize_poll(poll, viewer_id=user_id))


@polls_bp.post("/polls/<int:poll_id>/close")
@jwt_required()
def close_poll(poll_id):
    user_id = int(get_jwt_identity())
    poll = Poll.query.get_or_404(poll_id)
    chat = Chat.query.get_or_404(poll.chat_id)

    can_close = poll.creator_id == user_id
    if chat.type == "group":
        part = ChatParticipant.query.filter_by(chat_id=chat.id, user_id=user_id, role="admin").first()
        can_close = can_close or part is not None
    if chat.type == "channel":
        can_close = can_close or chat.owner_id == user_id

    if not can_close:
        return jsonify({"error": "Недостаточно прав"}), 403

    poll.is_closed = True
    db.session.commit()
    current_app.socketio.emit("poll_updated", {"poll_id": poll.id}, room=f"chat_{poll.chat_id}")
    return jsonify(serialize_poll(poll, viewer_id=user_id))
