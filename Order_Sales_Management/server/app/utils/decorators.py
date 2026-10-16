from functools import wraps
from flask import g, jsonify
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from ..extensions import db
from ..models import User
from .permissions import role_at_least

def _load_user(uid):
    if uid is None:
        return None
    try:
        return db.session.get(User, int(uid))
    except (TypeError, ValueError):
        return None

def _resolve_request_user():
    uid = get_jwt_identity()
    user = _load_user(uid)
    if user is None:
        return None, (jsonify(error="Invalid token"), 401)
    claims = get_jwt() or {}
    if claims.get("tv", 0) != user.token_version:
        return None, (jsonify(error="Invalid token"), 401)
    return user, None

def auth_required(fn):
    @wraps(fn)
    @jwt_required()
    def decorated(*args, **kwargs):
        user, err = _resolve_request_user()
        if err:
            return err
        g.current_user = user
        return fn(*args, **kwargs)
    return decorated

def role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            user, err = _resolve_request_user()
            if err:
                return err
            if user.role != required_role:
                return jsonify(error="Forbidden"), 403
            g.current_user = user
            return fn(*args, **kwargs)
        return decorated
    return wrapper

def min_role_required(required_role):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorated(*args, **kwargs):
            user, err = _resolve_request_user()
            if err:
                return err
            if not role_at_least(user.role, required_role):
                return jsonify(error="Forbidden"), 403
            g.current_user = user
            return fn(*args, **kwargs)
        return decorated
    return wrapper