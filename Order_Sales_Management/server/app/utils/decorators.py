from flask import g
from flask_jwt_extended import get_jwt_identity, jwt_required
from app import models
from app.extensions import db


def role_required(*roles: str):
    def decorator(fn):
        decorated = jwt_required()(fn)

        def _check_role(*args, **kwargs):
            role = get_jwt_role()
            if role not in roles:
                from flask import abort
                abort(403)
            return fn(*args, **kwargs)

        _check_role.__name__ = f"{fn.__name__}_requires_{'+'.join(sorted(roles))}"
        _check_role.__qualname__ = _check_role.__name__
        return _check_role

    return decorator


def current_user() -> models.User:
    if hasattr(g, "user") and g.user is not None:
        return g.user
    user_id = get_jwt_identity()
    if user_id is None:
        from flask import abort
        abort(401)
    g.user = db.session.get(models.User, int(user_id))
    if g.user is None:
        from flask import abort
        abort(401)
    return g.user


def get_jwt_role() -> str:
    claims = getattr(g, "_jwt_usr", None)
    if claims is None:
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        g._jwt_usr = claims
    return claims.get("role", "customer")
