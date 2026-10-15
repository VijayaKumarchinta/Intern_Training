from flask import Blueprint, jsonify, request

from ..extensions import jwt
from ..models import User
from ..services.auth_service import (
    forgot_password,
    link_customer,
    login,
    register,
    resend_verification_code,
    reset_password,
    verify_email,
)

auth = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth.route("/register", methods=["POST"])
def register_route():
    return register()


@auth.route("/verify", methods=["POST"])
def verify_route():
    return verify_email()


@auth.route("/resend-verification", methods=["POST"])
def resend_route():
    return resend_verification_code()


@auth.route("/link-customer", methods=["POST"])
def link_route():
    return link_customer()


@auth.route("/login", methods=["POST"])
def login_route():
    return login()


@auth.route("/forgot-password", methods=["POST"])
def forgot_route():
    return forgot_password()


@auth.route("/reset-password", methods=["POST"])
def reset_route():
    return reset_password()


@auth.route("/me", methods=["GET"])
def me_route():
    identity = jwt.get_jwt_identity()
    if identity is None:
        return jsonify(error="Not authenticated"), 401
    user = User.query.get(identity)
    if user is None:
        return jsonify(error="User not found"), 404
    return jsonify(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_verified=user.is_verified,
    ), 200
