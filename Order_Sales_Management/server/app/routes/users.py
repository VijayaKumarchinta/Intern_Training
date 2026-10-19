from flask import Blueprint, jsonify, request
from ..models import User
from ..extensions import db,hash_password
from ..utils.decorators import role_required
from ..constants import Role

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

@users_bp.get("")
@role_required(Role.ADMIN.value)
def list_users():
    users = User.query.order_by(User.id).all()
    return jsonify(users=[u.to_dict() for u in users]), 200

@users_bp.post("")
@role_required(Role.ADMIN.value)
def create_user():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "customer")
    
    if not email or not password:
        return jsonify(error="Email and password are required"), 400
        
    if User.query.filter(db.func.lower(User.email) == email.lower()).first():
        return jsonify(error="Email already registered"), 409
        
    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        full_name=data.get("full_name", "New User"),
        role=role,
        is_verified=True,
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user=user.to_dict()), 201

@users_bp.patch("/<int:user_id>/role")
@role_required(Role.ADMIN.value)
def update_user_role(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify(error="User not found"), 404

    data = request.get_json() or {}
    new_role = data.get("role")

    if new_role not in Role.values():
        return jsonify(error=f"Invalid role: {new_role}"), 400

    if user.role == Role.ADMIN.value and new_role == Role.CUSTOMER.value:
        admin_count = User.query.filter_by(role=Role.ADMIN.value).count()
        if admin_count <= 1:
            return jsonify(error="Cannot demote the last remaining admin"), 400

    user.role = new_role
    db.session.commit()

    return jsonify(message="Role updated", user=user.to_dict()), 200

@users_bp.delete("/<int:user_id>")
@role_required(Role.ADMIN.value)
def delete_user(user_id):
    from flask_jwt_extended import get_jwt_identity
    
    current_user_id = int(get_jwt_identity())
    if current_user_id == user_id:
        return jsonify(error="You cannot delete your own account"), 400

    user = db.session.get(User, user_id)
    if not user:
        return jsonify(error="User not found"), 404

    if user.role == Role.ADMIN.value:
        admin_count = User.query.filter_by(role=Role.ADMIN.value).count()
        if admin_count <= 1:
            return jsonify(error="Cannot delete the last remaining admin"), 400

    # Unlink any customer record so order history isn't lost
    if user.customer:
        user.customer.user_id = None
        db.session.add(user.customer)

    db.session.delete(user)
    db.session.commit()

    return jsonify(message="User deleted"), 200