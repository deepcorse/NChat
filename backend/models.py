from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint


db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(120), nullable=False)
    avatar_url = db.Column(db.String(255))
    status = db.Column(db.String(255), default="online")
    description = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_online = db.Column(db.Boolean, default=False, nullable=False)

    owned_chats = db.relationship("Chat", backref="owner", lazy=True)


class Chat(db.Model):
    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # private/group/channel
    title = db.Column(db.String(200))
    avatar = db.Column(db.String(255))
    description = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)


class ChatParticipant(db.Model):
    __tablename__ = "chat_participants"
    __table_args__ = (UniqueConstraint("user_id", "chat_id", name="uq_participant_user_chat"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.id"), nullable=False)
    role = db.Column(db.String(20), default="member")

    user = db.relationship("User", backref="chat_participations")
    chat = db.relationship("Chat", backref="participants")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    text = db.Column(db.Text)
    file_url = db.Column(db.String(255))
    file_type = db.Column(db.String(20))
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.Integer)
    reply_to_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    deleted = db.Column(db.Boolean, default=False, nullable=False)

    chat = db.relationship("Chat", backref="messages")
    sender = db.relationship("User", backref="messages")
    reply_to = db.relationship("Message", remote_side=[id], uselist=False)


class Reaction(db.Model):
    __tablename__ = "reactions"
    __table_args__ = (UniqueConstraint("message_id", "user_id", "reaction_type", name="uq_message_user_reaction"),)

    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey("messages.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reaction_type = db.Column(db.String(20), nullable=False)

    message = db.relationship("Message", backref="reactions")
    user = db.relationship("User", backref="reactions")


class ChannelSubscription(db.Model):
    __tablename__ = "channel_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "channel_id", name="uq_channel_subscription"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    channel_id = db.Column(db.Integer, db.ForeignKey("chats.id"), nullable=False)
    subscribed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref="channel_subscriptions")
    channel = db.relationship("Chat", backref="subscriptions")


class Story(db.Model):
    __tablename__ = "stories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    media_url = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # image/video
    caption = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False, index=True)

    user = db.relationship("User", backref="stories")


class StoryView(db.Model):
    __tablename__ = "story_views"
    __table_args__ = (UniqueConstraint("story_id", "viewer_id", name="uq_story_view"),)

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey("stories.id"), nullable=False)
    viewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    viewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    story = db.relationship("Story", backref="views")
    viewer = db.relationship("User", backref="story_views")
