from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from ..models import User

def _load_user(uid):
    if uid is None:
        return None
    try:
        return User.query.get(int(uid))
    except (TypeError, ValueError):
        return None

def role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            claims = get_jwt() if isinstance(get_jwt(), dict) else {}
            if claims.get("role") != required_role:
                return jsonify(error="Forbidden"), 403
            return fn(*args, **kwargs)

        return decorated

    return wrapper

def get_current_user():
    uid = get_jwt_identity()
    if uid is None:
        return None
    return _load_user(uid)
