from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import Story, StoryView, User, db
from ..utils import save_upload

stories_bp = Blueprint("stories", __name__)


@stories_bp.post("")
@jwt_required()
def create_story():
    user_id = int(get_jwt_identity())
    media = request.files.get("media")
    if not media:
        return jsonify({"error": "Нужно прикрепить фото или видео"}), 400

    try:
        file_data = save_upload(media, "stories")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    if file_data["file_type"] not in {"image", "video"}:
        return jsonify({"error": "Stories поддерживают только фото и видео"}), 400

    now = datetime.utcnow()
    story = Story(
        user_id=user_id,
        media_url=file_data["url"],
        media_type=file_data["file_type"],
        caption=(request.form.get("caption") or "").strip()[:255],
        created_at=now,
        expires_at=now + timedelta(hours=24),
    )
    db.session.add(story)
    db.session.commit()

    return jsonify({"story_id": story.id, "expires_at": story.expires_at.isoformat()}), 201


@stories_bp.get("/feed")
@jwt_required()
def get_feed():
    user_id = int(get_jwt_identity())
    now = datetime.utcnow()

    active = (
        Story.query.filter(Story.expires_at > now)
        .order_by(Story.created_at.desc())
        .all()
    )

    grouped = {}
    for s in active:
        owner = User.query.get(s.user_id)
        if s.user_id not in grouped:
            grouped[s.user_id] = {
                "user_id": s.user_id,
                "nickname": owner.nickname if owner else "Unknown",
                "avatar": owner.avatar_url if owner else None,
                "stories": [],
            }

        seen = StoryView.query.filter_by(story_id=s.id, viewer_id=user_id).first() is not None
        grouped[s.user_id]["stories"].append(
            {
                "id": s.id,
                "media_url": s.media_url,
                "media_type": s.media_type,
                "caption": s.caption,
                "created_at": s.created_at.isoformat(),
                "expires_at": s.expires_at.isoformat(),
                "seen": seen,
            }
        )

    return jsonify(list(grouped.values()))


@stories_bp.get("/<int:story_id>")
@jwt_required()
def get_story(story_id):
    user_id = int(get_jwt_identity())
    story = Story.query.get_or_404(story_id)
    if story.expires_at <= datetime.utcnow():
        return jsonify({"error": "Story истекла"}), 410

    if not StoryView.query.filter_by(story_id=story_id, viewer_id=user_id).first():
        db.session.add(StoryView(story_id=story_id, viewer_id=user_id))
        db.session.commit()

    owner = User.query.get(story.user_id)
    return jsonify(
        {
            "id": story.id,
            "user_id": story.user_id,
            "nickname": owner.nickname if owner else "Unknown",
            "avatar": owner.avatar_url if owner else None,
            "media_url": story.media_url,
            "media_type": story.media_type,
            "caption": story.caption,
            "created_at": story.created_at.isoformat(),
            "expires_at": story.expires_at.isoformat(),
            "views": StoryView.query.filter_by(story_id=story_id).count(),
        }
    )


@stories_bp.delete("/<int:story_id>")
@jwt_required()
def delete_story(story_id):
    user_id = int(get_jwt_identity())
    story = Story.query.get_or_404(story_id)
    if story.user_id != user_id:
        return jsonify({"error": "Можно удалять только свои stories"}), 403

    StoryView.query.filter_by(story_id=story_id).delete()
    db.session.delete(story)
    db.session.commit()
    return jsonify({"message": "Story удалена"})
