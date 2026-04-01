from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from ..utils import list_sticker_packs

stickers_bp = Blueprint("stickers", __name__)


@stickers_bp.get("")
@jwt_required()
def sticker_packs():
    # Папка со стикерами перечитывается на каждый запрос,
    # поэтому изменения на диске доступны без рестарта (в т.ч. каждые 30 минут).
    return jsonify(list_sticker_packs())
