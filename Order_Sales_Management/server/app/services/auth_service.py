import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from flask import current_app
from flask_jwt_extended import create_access_token
from ..constants import Role
from ..extensions import db, hash_password, verify_password
from ..models import Customer, User
from ..utils.email import send_password_reset, send_verification_code
from ..utils.validators import normalize_email, validate_email, validate_password

log = logging.getLogger(__name__)


def _now():
    return datetime.now(timezone.utc)


def _hash(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _new_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def _new_reset_token():
    return secrets.token_urlsafe(32)


def _verify_ttl_minutes():
    return current_app.config.get("VERIFY_TTL_MINUTES", 2)


def _verify_max_attempts():
    return current_app.config.get("VERIFY_MAX_ATTEMPTS", 3)


def _reset_ttl_hours():
    return current_app.config.get("RESET_TTL_HOURS", 1)


def _check_customer_ownership(customer_id, email, current_user_id=None):
    """
    Validate that the caller may claim this customer_id.

    Returns (cust, error_message).

    Rules (in order):
      1. Customer must exist.
      2. If already linked to a *different* user -> reject.
      3. If already linked to *this* user -> allow (idempotent).
      4. Customer must have an email on file (NULL -> reject; legacy/imported).
      5. That email must exactly match the registering email.
    """
    customer_id = (customer_id or "").strip().upper()
    if not customer_id:
        return None, "customer_id is required"

    cust = db.session.get(Customer, customer_id)
    if cust is None:
        return None, "Unknown Customer ID"

    if cust.user_id is not None and cust.user_id != current_user_id:
        return None, "This Customer ID is already linked to another account"

    if cust.email is None or str(cust.email).strip() == "":
        return None, (
            "This customer record has no email on file. "
            "Please contact support to link your account."
        )

    if normalize_email(cust.email) != normalize_email(email):
        return None, "Email does not match the customer record for this ID"

    return cust, None


def register(email, password, full_name, customer_id=None):
    """
    Register a new user account (with optional loyalty customer_id).

    The customer is NOT linked at register time — that happens after OTP
    verification succeeds, so an attacker cannot bind a customer ID to an
    account before proving they control the corresponding inbox.
    """
    email = normalize_email(email)
    full_name = (full_name or "").strip()
    customer_id = (customer_id or "").strip().upper() or None

    err = validate_email(email)
    if err:
        return None, err
    err = validate_password(password)
    if err:
        return None, err

    if User.query.filter(db.func.lower(User.email) == email).first():
        return None, "Email already registered"

    # Pre-validate the customer claim so we never send an OTP for a
    # doomed registration (bad ID, wrong email, already linked, no email).
    if customer_id is not None:
        _cust, err = _check_customer_ownership(customer_id, email, current_user_id=None)
        if err:
            return None, err

    code = _new_otp()
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=Role.CUSTOMER.value,
        is_verified=False,
        verification_token_hash=_hash(code),
        verification_expires_at=_now() + timedelta(minutes=_verify_ttl_minutes()),
        verification_attempts=0,
    )
    db.session.add(user)
    db.session.commit()

    send_verification_code(email, code)
    log.info("Register: user=%s customer=%s", user.id, customer_id)
    return user, None


def verify_email(email, code, customer_id=None):
    """
    Verify a user's email with an OTP. If customer_id is supplied, link the
    customer to the user *after* OTP validation succeeds.
    """
    email = normalize_email(email)
    code = (code or "").strip()
    customer_id = (customer_id or "").strip().upper() or None

    if not email or not code:
        return None, "Email and code are required"

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if user is None:
        return None, "Invalid code"
    if user.is_verified:
        return None, "Email already verified"
    if not user.verification_token_hash:
        return None, "No pending verification"
    if user.verification_expires_at is None or user.verification_expires_at < _now():
        return None, "Code expired"

    max_attempts = _verify_max_attempts()
    if user.verification_attempts >= max_attempts:
        return None, "Too many attempts - request a new code"

    if not secrets.compare_digest(user.verification_token_hash, _hash(code)):
        user.verification_attempts += 1
        db.session.commit()
        remaining = max_attempts - user.verification_attempts
        return None, f"Invalid code ({remaining} attempts remaining)"

    # OTP is correct. Now perform the ownership check + link if requested.
    if customer_id is not None:
        cust, err = _check_customer_ownership(customer_id, email, current_user_id=user.id)
        if err:
            # OTP was correct, but the claim is invalid. Mark verified,
            # do NOT link, and tell the caller what went wrong.
            user.is_verified = True
            user.verification_token_hash = None
            user.verification_expires_at = None
            user.verification_attempts = 0
            db.session.commit()
            log.warning(
                "Verify: user=%s verified but link failed for customer=%s: %s",
                user.id, customer_id, err,
            )
            return None, err

        cust.user_id = user.id
        if not cust.cust_name:
            cust.cust_name = user.full_name or user.email

    user.is_verified = True
    user.verification_token_hash = None
    user.verification_expires_at = None
    user.verification_attempts = 0
    db.session.commit()

    log.info("Verify: user=%s verified customer=%s", user.id, customer_id)
    return user, None


def resend_verification_code(email):
    email = normalize_email(email)
    if not email:
        return False, "Email is required"

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if user is None or user.is_verified:
        return True, None

    code = _new_otp()
    user.verification_token_hash = _hash(code)
    user.verification_expires_at = _now() + timedelta(minutes=_verify_ttl_minutes())
    user.verification_attempts = 0
    db.session.commit()

    send_verification_code(email, code)
    log.info("Resend: user=%s", user.id)
    return True, None


def login(email, password):
    email = normalize_email(email)
    if not email or not password:
        return None, "Email and password are required"

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if user is None:
        return None, "Invalid credentials"
    if not verify_password(password, user.password_hash):
        return None, "Invalid credentials"
    if not user.is_verified:
        return None, "Please verify your email first"

    token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role,
            "email": user.email,
            "tv": user.token_version,
        },
    )
    log.info("Login: user=%s", user.id)
    return {"access_token": token, "user": user}, None


def forgot_password(email):
    email = normalize_email(email)
    if not email:
        return False, "Email is required"

    user = User.query.filter(db.func.lower(User.email) == email).first()
    if user is None:
        return True, None

    token = _new_reset_token()
    user.reset_token_hash = _hash(token)
    user.reset_token_expires_at = _now() + timedelta(hours=_reset_ttl_hours())
    db.session.commit()

    send_password_reset(email, token)
    log.info("Forgot: user=%s", user.id)
    return True, None


def reset_password(token, new_password):
    token = (token or "").strip()
    if not token:
        return False, "Token is required"
    err = validate_password(new_password)
    if err:
        return False, err

    user = User.query.filter_by(reset_token_hash=_hash(token)).first()
    if user is None:
        return False, "Invalid or expired token"
    if user.reset_token_expires_at is None or user.reset_token_expires_at < _now():
        return False, "Token expired"

    user.password_hash = hash_password(new_password)
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    user.verification_token_hash = None
    user.verification_expires_at = None
    user.verification_attempts = 0
    user.token_version = user.token_version + 1
    db.session.commit()

    log.info("Reset: user=%s", user.id)
    return True, None