from flask import Blueprint, jsonify
from ..models import User
from ..utils.decorators import role_required
from ..constants import Role

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.get("")
@role_required(Role.ADMIN.value)
def list_users():
    users = User.query.order_by(User.id).all()
    return jsonify(users=[u.to_dict() for u in users]), 200