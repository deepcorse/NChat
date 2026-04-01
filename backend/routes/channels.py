from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Chat, ChannelSubscription, db
from ..utils import save_upload

channels_bp = Blueprint("channels", __name__)


@channels_bp.post("")
@jwt_required()
def create_channel():
    user_id = int(get_jwt_identity())
    existing = Chat.query.filter_by(type="channel", owner_id=user_id).first()
    if existing:
        return jsonify({"error": "У вас уже есть канал", "channel_id": existing.id}), 409

    title = (request.form.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Название обязательно"}), 400

    channel = Chat(type="channel", title=title, description=(request.form.get("description") or "").strip(), owner_id=user_id)
    avatar = request.files.get("avatar")
    if avatar:
        try:
            channel.avatar = save_upload(avatar, "channels")["url"]
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    db.session.add(channel)
    db.session.commit()
    return jsonify({"channel_id": channel.id}), 201


@channels_bp.get("/<int:channel_id>")
@jwt_required()
def get_channel(channel_id):
    channel = Chat.query.get_or_404(channel_id)
    if channel.type != "channel":
        return jsonify({"error": "Это не канал"}), 400

    subs = ChannelSubscription.query.filter_by(channel_id=channel_id).count()
    return jsonify({
        "id": channel.id,
        "title": channel.title,
        "description": channel.description,
        "avatar": channel.avatar,
        "owner_id": channel.owner_id,
        "subscribers": subs,
    })


@channels_bp.post("/<int:channel_id>/subscribe")
@jwt_required()
def subscribe(channel_id):
    user_id = int(get_jwt_identity())
    channel = Chat.query.get_or_404(channel_id)
    if channel.type != "channel":
        return jsonify({"error": "Это не канал"}), 400

    sub = ChannelSubscription.query.filter_by(user_id=user_id, channel_id=channel_id).first()
    if sub:
        db.session.delete(sub)
        db.session.commit()
        return jsonify({"subscribed": False})

    db.session.add(ChannelSubscription(user_id=user_id, channel_id=channel_id))
    db.session.commit()
    return jsonify({"subscribed": True})


@channels_bp.delete("/<int:channel_id>")
@jwt_required()
def delete_channel(channel_id):
    user_id = int(get_jwt_identity())
    channel = Chat.query.get_or_404(channel_id)
    if channel.type != "channel":
        return jsonify({"error": "Это не канал"}), 400
    if channel.owner_id != user_id:
        return jsonify({"error": "Только владелец"}), 403

    ChannelSubscription.query.filter_by(channel_id=channel_id).delete()
    db.session.delete(channel)
    db.session.commit()
    return jsonify({"message": "Канал удален"})
