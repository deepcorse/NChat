from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import join_room

from .models import ChatParticipant, ChannelSubscription, User, db


def register_socket_handlers(socketio):
    @socketio.on("connect")
    def handle_connect(auth):
        token = (auth or {}).get("token") if isinstance(auth, dict) else None
        if not token:
            return False
        try:
            user_id = int(decode_token(token)["sub"])
        except Exception:
            return False

        user = User.query.get(user_id)
        if not user:
            return False

        user.is_online = True
        db.session.commit()

        chats = [p.chat_id for p in ChatParticipant.query.filter_by(user_id=user_id).all()]
        chats += [s.channel_id for s in ChannelSubscription.query.filter_by(user_id=user_id).all()]
        for chat_id in set(chats):
            join_room(f"chat_{chat_id}")
        join_room(f"user_{user_id}")

    @socketio.on("join_chat")
    def join_chat(data):
        chat_id = data.get("chat_id")
        if chat_id:
            join_room(f"chat_{chat_id}")
