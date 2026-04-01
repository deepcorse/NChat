from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Chat, ChatParticipant, User, db
from ..utils import save_upload

groups_bp = Blueprint("groups", __name__)


def _is_admin(user_id, group_id):
    p = ChatParticipant.query.filter_by(user_id=user_id, chat_id=group_id).first()
    return p and p.role == "admin"


@groups_bp.post("")
@jwt_required()
def create_group():
    user_id = int(get_jwt_identity())
    title = (request.form.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Название обязательно"}), 400

    group = Chat(type="group", title=title, description=(request.form.get("description") or "").strip(), owner_id=user_id)
    avatar = request.files.get("avatar")
    if avatar:
        try:
            group.avatar = save_upload(avatar, "groups")["url"]
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

    db.session.add(group)
    db.session.flush()
    db.session.add(ChatParticipant(user_id=user_id, chat_id=group.id, role="admin"))

    for uid in request.form.getlist("members"):
        if uid.isdigit() and int(uid) != user_id and User.query.get(int(uid)):
            db.session.add(ChatParticipant(user_id=int(uid), chat_id=group.id, role="member"))
    db.session.commit()
    return jsonify({"group_id": group.id}), 201


@groups_bp.post("/<int:group_id>/members")
@jwt_required()
def add_member(group_id):
    user_id = int(get_jwt_identity())
    group = Chat.query.get_or_404(group_id)
    if group.type != "group":
        return jsonify({"error": "Это не группа"}), 400
    if not _is_admin(user_id, group_id):
        return jsonify({"error": "Только админ"}), 403

    new_user_id = (request.get_json() or {}).get("user_id")
    if not new_user_id or not User.query.get(new_user_id):
        return jsonify({"error": "Пользователь не найден"}), 404

    if ChatParticipant.query.filter_by(user_id=new_user_id, chat_id=group_id).first():
        return jsonify({"message": "Уже участник"})

    db.session.add(ChatParticipant(user_id=new_user_id, chat_id=group_id, role="member"))
    db.session.commit()
    return jsonify({"message": "Участник добавлен"})


@groups_bp.delete("/<int:group_id>/members/<int:member_id>")
@jwt_required()
def remove_member(group_id, member_id):
    user_id = int(get_jwt_identity())
    if not _is_admin(user_id, group_id):
        return jsonify({"error": "Только админ"}), 403
    participant = ChatParticipant.query.filter_by(user_id=member_id, chat_id=group_id).first_or_404()
    db.session.delete(participant)
    db.session.commit()
    return jsonify({"message": "Участник удалён"})


@groups_bp.patch("/<int:group_id>")
@jwt_required()
def patch_group(group_id):
    user_id = int(get_jwt_identity())
    if not _is_admin(user_id, group_id):
        return jsonify({"error": "Только админ"}), 403

    group = Chat.query.get_or_404(group_id)
    data = request.get_json() or {}
    group.title = (data.get("title") or group.title).strip()
    group.description = (data.get("description") or group.description).strip()
    db.session.commit()
    return jsonify({"message": "Группа обновлена"})
