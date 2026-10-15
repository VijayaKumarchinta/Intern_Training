import hashlib
import logging
import random
import secrets
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, jsonify

from ..extensions import bcrypt, db
from ..models import Customer, User
from ..utils.email import send_password_reset, send_verification_code

log = logging.getLogger(__name__)

auth_service = Blueprint("auth_service", __name__, url_prefix="/api/auth")

VERIFY_TTL_MINUTES = 2
VERIFY_MAX_ATTEMPTS = 3
RESET_TTL_HOURS = 1

from flask import current_app


def _verify_ttl():
    return current_app.config.get("VERIFY_TTL_MINUTES", VERIFY_TTL_MINUTES)


def _verify_max_attempts():
    return current_app.config.get("VERIFY_MAX_ATTEMPTS", VERIFY_MAX_ATTEMPTS)


def _reset_ttl_hours():
    return current_app.config.get("RESET_TTL_HOURS", RESET_TTL_HOURS)


def _now():
    return datetime.now(timezone.utc)


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _new_otp():
    return f"{random.randint(0, 999999):06d}"


def _new_reset_token():
    return secrets.token_urlsafe(32)


def register():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""
    full_name = (body.get("full_name") or "").strip()
    customer_id = (body.get("customer_id") or "").strip()

    if not email or "@" not in email:
        return jsonify(error="Invalid email"), 400
    if not password or len(password) < 8:
        return jsonify(error="Password must be at least 8 characters"), 400
    if not customer_id:
        return jsonify(error="customer_id is required"), 400

    existing = User.query.filter(db.func.lower(User.email) == email).first()
    if existing:
        return jsonify(error="Email already registered"), 409

    cust = Customer.query.get(customer_id)
    if cust is None:
        return jsonify(error="Unknown Customer ID"), 404
    if cust.user_id is not None:
        return jsonify(error="This Customer ID is already linked to another account"), 409

    code = _new_otp()
    user = User(
        email=email,
        password_hash=bcrypt.hash(password),
        full_name=full_name,
        role="customer",
        is_verified=False,
        verification_token_hash=_hash(code),
        verification_expires_at=_now() + timedelta(minutes=VERIFY_TTL_MINUTES),
        verification_attempts=0,
    )
    db.session.add(user)
    db.session.commit()

    send_verification_code(email, code)
    log.info("Register: created user %s for customer %s", user.id, customer_id)

    return jsonify(
        message="Verification code sent",
        user_id=user.id,
        email=user.email,
        is_verified=False,
    ), 201


def verify_email():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    code = (body.get("code") or "").strip()

    if not email or not code:
        return jsonify(error="Email and code are required"), 400

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if user is None:
        log.warning("Verify: no user for email %s", email)
        return jsonify(error="Invalid code"), 400
    if user.is_verified:
        return jsonify(error="Email already verified"), 400
    if not user.verification_token_hash:
        return jsonify(error="No pending verification"), 400
    if user.verification_expires_at is None or user.verification_expires_at < _now():
        return jsonify(error="Code expired"), 400
    if user.verification_attempts >= _verify_max_attempts():
        return jsonify(error="Too many attempts - request a new code"), 400

    if user.verification_token_hash != _hash(code):
        user.verification_attempts += 1
        db.session.commit()
        remaining = VERIFY_MAX_ATTEMPTS - user.verification_attempts
        log.warning("Verify: wrong code for %s, attempts=%d", email, user.verification_attempts)
        return jsonify(error=f"Invalid code ({remaining} attempts remaining)"), 400

    user.is_verified = True
    user.verification_token_hash = None
    user.verification_expires_at = None
    user.verification_attempts = 0
    db.session.commit()

    log.info("Verify: verified user %s", user.id)
    return jsonify(message="Email verified", user_id=user.id, is_verified=True), 200


def resend_verification_code():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()

    if not email:
        return jsonify(error="Email is required"), 400

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if user is None or user.is_verified:
        return jsonify(message="If the email exists and is unverified, a new code was sent"), 200

    code = _new_otp()
    user.verification_token_hash = _hash(code)
    user.verification_expires_at = _now() + timedelta(minutes=_verify_ttl())
    user.verification_attempts = 0
    db.session.commit()

    send_verification_code(email, code)
    log.info("Resend: new verification code for user %s", user.id)
    return jsonify(message="If the email exists and is unverified, a new code was sent"), 200


def link_customer():
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id")
    customer_id = (body.get("customer_id") or "").strip()

    if not user_id or not customer_id:
        return jsonify(error="user_id and customer_id are required"), 400

    user = User.query.get(user_id)
    if user is None:
        return jsonify(error="User not found"), 404
    if not user.is_verified:
        return jsonify(error="User must be verified before linking a customer"), 403

    cust = Customer.query.get(customer_id)
    if cust is None:
        return jsonify(error="Unknown Customer ID"), 404
    if cust.user_id is not None and cust.user_id != user.id:
        return jsonify(error="This Customer ID is already linked to another account"), 409

    cust.user_id = user.id
    cust.email = user.email
    if not cust.cust_name:
        cust.cust_name = user.full_name or user.email

    db.session.commit()
    log.info("Link: linked customer %s to user %s", customer_id, user.id)
    return jsonify(message="Customer linked", customer_id=customer_id, user_id=user.id), 200


def login():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    password = body.get("password") or ""

    if not email or not password:
        return jsonify(error="Email and password are required"), 400

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if user is None:
        return jsonify(error="Invalid credentials"), 401
    if not bcrypt.verify(password, user.password_hash):
        return jsonify(error="Invalid credentials"), 401
    if not user.is_verified:
        return jsonify(error="Please verify your email first"), 403

    from flask_jwt_extended import create_access_token

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email},
    )
    log.info("Login: user %s authenticated", user.id)
    return jsonify(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        role=user.role,
        is_verified=True,
    ), 200


def forgot_password():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()

    if not email:
        return jsonify(error="Email is required"), 400

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if user is None:
        log.info("Forgot: no account for email %s", email)
        return jsonify(message="If the email exists, a reset link was sent"), 200

    token = _new_reset_token()
    user.reset_token_hash = _hash(token)
    user.reset_token_expires_at = _now() + timedelta(hours=_reset_ttl_hours())
    db.session.commit()

    send_password_reset(email, token)
    log.info("Forgot: reset link sent for user %s", user.id)
    return jsonify(message="If the email exists, a reset link was sent"), 200


def reset_password():
    body = request.get_json(silent=True) or {}
    token = (body.get("token") or "").strip()
    new_password = body.get("new_password") or ""

    if not token:
        return jsonify(error="Token is required"), 400
    if not new_password or len(new_password) < 8:
        return jsonify(error="Password must be at least 8 characters"), 400

    token_hash = _hash(token)
    user = User.query.filter_by(reset_token_hash=token_hash).first()
    if user is None:
        log.warning("Reset: invalid reset token")
        return jsonify(error="Invalid or expired token"), 400
    if user.reset_token_expires_at is None or user.reset_token_expires_at < _now():
        return jsonify(error="Token expired"), 400

    user.password_hash = bcrypt.hash(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.session.commit()

    log.info("Reset: password reset for user %s", user.id)
    return jsonify(message="Password reset successful", user_id=user.id), 200


def _build_user_response(user):
    return jsonify(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_verified=user.is_verified,
    )


@auth_service.route("/register", methods=["POST"])
def register_route():
    return register()


@auth_service.route("/verify", methods=["POST"])
def verify_route():
    return verify_email()


@auth_service.route("/resend-verification", methods=["POST"])
def resend_route():
    return resend_verification_code()


@auth_service.route("/link-customer", methods=["POST"])
def link_route():
    return link_customer()


@auth_service.route("/login", methods=["POST"])
def login_route():
    return login()


@auth_service.route("/forgot-password", methods=["POST"])
def forgot_route():
    return forgot_password()


@auth_service.route("/reset-password", methods=["POST"])
def reset_route():
    return reset_password()


@auth_service.route("/me", methods=["GET"])
def me_route():
    from flask_jwt_extended import get_jwt_identity

    uid = get_jwt_identity()
    if uid is None:
        return jsonify(error="Not authenticated"), 401

    user = User.query.get(uid)
    if user is None:
        return jsonify(error="User not found"), 404

    return _build_user_response(user)
