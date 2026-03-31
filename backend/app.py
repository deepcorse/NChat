import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_socketio import SocketIO

from .auth import auth_bp
from .config import Config
from .models import db
from .routes.channels import channels_bp
from .routes.chats import chats_bp
from .routes.groups import groups_bp
from .routes.messages import messages_bp
from .routes.reactions import reactions_bp
from .routes.stories import stories_bp
from .routes.users import users_bp
from .websocket import register_socket_handlers


def create_app():
    app = Flask(__name__, static_folder="../frontend", static_url_path="/")
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    CORS(app)
    db.init_app(app)
    JWTManager(app)
    CSRFProtect(app)

    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
    app.socketio = socketio
    register_socket_handlers(socketio)

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(chats_bp, url_prefix="/api/chats")
    app.register_blueprint(groups_bp, url_prefix="/api/groups")
    app.register_blueprint(channels_bp, url_prefix="/api/channels")
    app.register_blueprint(messages_bp, url_prefix="/api/messages")
    app.register_blueprint(reactions_bp, url_prefix="/api/messages")
    app.register_blueprint(stories_bp, url_prefix="/api/stories")

    @app.route("/uploads/<path:filename>")
    def uploads(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/")
    def root():
        return app.send_static_file("index.html")

    @app.errorhandler(413)
    def too_large(_):
        return jsonify({"error": "Файл слишком большой (макс. 20 МБ)"}), 413

    with app.app_context():
        db.create_all()

    return app, socketio


if __name__ == "__main__":
    app, socketio = create_app()
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
