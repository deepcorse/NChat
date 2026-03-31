from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from .models import User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    login = (data.get("login") or "").strip().lower()
    password = data.get("password") or ""
    nickname = (data.get("nickname") or "").strip()

    if len(login) < 3 or len(password) < 6 or not nickname:
        return jsonify({"error": "Некорректные данные регистрации"}), 400

    if User.query.filter_by(login=login).first():
        return jsonify({"error": "Логин уже занят"}), 409

    user = User(login=login, password_hash=generate_password_hash(password), nickname=nickname, is_online=True)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": {"id": user.id, "login": user.login, "nickname": user.nickname}}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    login = (data.get("login") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(login=login).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Неверный логин или пароль"}), 401

    user.is_online = True
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": {"id": user.id, "login": user.login, "nickname": user.nickname}})


@auth_bp.get("/logout")
@jwt_required()
def logout():
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    user.is_online = False
    db.session.commit()
    return jsonify({"message": "Выход выполнен"})


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get_or_404(int(get_jwt_identity()))
    return jsonify({
        "id": user.id,
        "login": user.login,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "status": user.status,
        "description": user.description,
        "is_online": user.is_online,
    })
