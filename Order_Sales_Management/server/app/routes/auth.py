from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from ..utils.decorators import get_current_user
from ..services.auth_service import (
    register,
    verify_email,
    resend_verification_code,
    link_customer,
    login,
    forgot_password,
    reset_password,
)
from ..extensions import jwt

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _json():
    return request.get_json(silent=True) or {}


@auth_bp.post("/register")
def register_route():
    body = _json()
    user, err = register(
        body.get("email"),
        body.get("password"),
        body.get("full_name"),
        body.get("customer_id"),
    )
    if err:
        return jsonify(error=err), 400
    return jsonify(
        message="Verification code sent",
        user_id=user.id,
        email=user.email,
        is_verified=False,
    ), 201


@auth_bp.post("/verify")
def verify_route():
    body = _json()
    user, err = verify_email(body.get("email"), body.get("code"))
    if err:
        return jsonify(error=err), 400

    customer_id = body.get("customer_id")
    if customer_id:
        ok, err = link_customer(user, customer_id)
        if not ok:
            return jsonify(error=err), 409

    return jsonify(message="Email verified", user_id=user.id, is_verified=True), 200


@auth_bp.post("/resend-verification")
def resend_route():
    body = _json()
    resend_verification_code(body.get("email"))
    return jsonify(message="If the email needs verification, a new code was sent"), 200


@auth_bp.post("/login")
def login_route():
    body = _json()
    result, err = login(body.get("email"), body.get("password"))
    if err:
        return jsonify(error=err), 401
    return jsonify(
        access_token=result["access_token"],
        user=result["user"].to_dict(),
    ), 200


@auth_bp.post("/forgot-password")
def forgot_route():
    body = _json()
    forgot_password(body.get("email"))
    return jsonify(message="If the email exists, a reset link was sent"), 200


@auth_bp.post("/reset-password")
def reset_route():
    body = _json()
    ok, err = reset_password(body.get("token"), body.get("new_password"))
    if not ok:
        return jsonify(error=err), 400
    return jsonify(message="Password reset successful"), 200


@auth_bp.get("/me")
@jwt_required()
def me_route():
    user = get_current_user()
    if user is None:
        return jsonify(error="User not found"), 404
    data = user.to_dict()
    if user.customer is not None:
        data["customer"] = {
            "customer_id": user.customer.customer_id,
            "cust_name": user.customer.cust_name,
        }
    return jsonify(data), 200
