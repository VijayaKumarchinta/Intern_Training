from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity

from app import models
from app.services.auth_service import (
    register,
    verify_email,
    authenticate,
    request_password_reset,
    reset_password,
    get_current_user,
)

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register_route():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password")
    full_name = (body.get("full_name") or "").strip() or None
    customer_id = (body.get("customer_id") or "").strip().upper() or None

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400

    try:
        token = register(email, password, full_name=full_name, customer_id=customer_id)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409

    return jsonify({"message": "registeration pending verification", "token": token}), 201


@auth_bp.route("/verify/<token>", methods=["GET"])
def verify_route(token):
    try:
        verify_email(token)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"message": "email verified"}), 200


@auth_bp.route("/login", methods=["POST"])
def login_route():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    try:
        user, access_token = authenticate(email, password)
    except ValueError as exc:
        return jsonify({"error": "invalid credentials"}), 401

    if not user.is_verified:
        return jsonify({"error": "email not verified"}), 403

    return jsonify({"user": _user_json(user), "access_token": access_token}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password_route():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "email is required"}), 400

    token = request_password_reset(email)
    if token is None:
        return jsonify({"message": "if that email exists, a reset link has been sent"}), 200
    return jsonify({"message": "if that email exists, a reset link has been sent"}), 200


@auth_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password_route(token):
    body = request.get_json(silent=True) or {}
    new_password = body.get("password")
    if not new_password:
        return jsonify({"error": "password is required"}), 400
    if len(new_password) < 8:
        return jsonify({"error": "password must be at least 8 characters"}), 400

    try:
        reset_password(token, new_password)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify({"message": "password reset successful"}), 200


@auth_bp.route("/me", methods=["GET"])
def me_route():
    user_id = get_jwt_identity()
    if user_id is None:
        return jsonify({"error": "unauthorized"}), 401
    user = get_current_user(user_id)
    if user is None:
        return jsonify({"error": "user not found"}), 404
    return jsonify(_user_json(user)), 200


def _user_json(user: models.User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "is_verified": user.is_verified,
    }
