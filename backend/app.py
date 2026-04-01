import os
import sys

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO
from sqlalchemy import text

# Поддерживаем оба способа запуска:
# 1) python -m backend.app
# 2) python backend/app.py
if __package__ is None or __package__ == "":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from backend.auth import auth_bp
    from backend.config import Config
    from backend.models import db
    from backend.routes.admin import admin_bp
    from backend.routes.channels import channels_bp
    from backend.routes.chats import chats_bp
    from backend.routes.groups import groups_bp
    from backend.routes.messages import messages_bp
    from backend.routes.reactions import reactions_bp
    from backend.routes.stickers import stickers_bp
    from backend.routes.stories import stories_bp
    from backend.routes.users import users_bp
    from backend.websocket import register_socket_handlers
else:
    from .auth import auth_bp
    from .config import Config
    from .models import db
    from .routes.admin import admin_bp
    from .routes.channels import channels_bp
    from .routes.chats import chats_bp
    from .routes.groups import groups_bp
    from .routes.messages import messages_bp
    from .routes.reactions import reactions_bp
    from .routes.stickers import stickers_bp
    from .routes.stories import stories_bp
    from .routes.users import users_bp
    from .websocket import register_socket_handlers


def _ensure_reply_to_column():
    cols = db.session.execute(text("PRAGMA table_info(messages)")).fetchall()
    col_names = {col[1] for col in cols}
    if "reply_to_id" not in col_names:
        db.session.execute(text("ALTER TABLE messages ADD COLUMN reply_to_id INTEGER"))
        db.session.commit()


def create_app():
    app = Flask(__name__, static_folder="../frontend", static_url_path="/")
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app)
    db.init_app(app)
    JWTManager(app)
    csrf = CSRFProtect(app)

    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
    app.socketio = socketio
    register_socket_handlers(socketio)

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(chats_bp, url_prefix="/api/chats")
    app.register_blueprint(groups_bp, url_prefix="/api/groups")
    app.register_blueprint(channels_bp, url_prefix="/api/channels")
    app.register_blueprint(messages_bp, url_prefix="/api/messages")
    app.register_blueprint(reactions_bp, url_prefix="/api/messages")
    app.register_blueprint(stories_bp, url_prefix="/api/stories")
    app.register_blueprint(stickers_bp, url_prefix="/api/stickers")

    # JWT-based API routes work without CSRF form tokens.
    csrf.exempt(auth_bp)
    csrf.exempt(admin_bp)
    csrf.exempt(users_bp)
    csrf.exempt(chats_bp)
    csrf.exempt(groups_bp)
    csrf.exempt(channels_bp)
    csrf.exempt(messages_bp)
    csrf.exempt(reactions_bp)
    csrf.exempt(stories_bp)
    csrf.exempt(stickers_bp)

    @app.route("/uploads/<path:filename>")
    def uploads(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/stickers/<path:filename>")
    def stickers(filename):
        stickers_dir = os.path.join(app.root_path, "stickers")
        return send_from_directory(stickers_dir, filename)

    @app.route("/")
    def root():
        return app.send_static_file("index.html")

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"error": "Файл слишком большой (макс. 20 МБ)"}), 413

    with app.app_context():
        db.create_all()
        _ensure_reply_to_column()

    return app, socketio


if __name__ == "__main__":
    app, socketio = create_app()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
