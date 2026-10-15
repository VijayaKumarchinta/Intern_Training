from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity
from jwt import InvalidTokenError

from . import _null_user
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
        def decorated(*args, **kwargs):
            try:
                claims = get_jwt()
            except InvalidTokenError:
                return jsonify(error="Invalid or missing token"), 401

            role = claims.get("role") if isinstance(claims, dict) else None
            if role != required_role:
                return jsonify(error="Forbidden"), 403

            return fn(*args, **kwargs)

        return decorated

    return wrapper

def current_user():
    uid = get_jwt_identity()
    return _load_user(uid)

def customer_user():
    user = current_user()
    if user is None:
        return None
    if user.role != "customer":
        return None
    return user
