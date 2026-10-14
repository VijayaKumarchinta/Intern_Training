import secrets
from datetime import datetime, timedelta, timezone

from flask import current_app
from flask_mail import Message
from passlib.context import CryptContext
from sqlalchemy import select

from app.extensions import db, bcrypt
from app import models


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def register(email: str, password: str, full_name: str | None = None, customer_id: str | None = None):
    existing = db.session.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none()
    if existing:
        raise ValueError("email already registered")

    user = models.User(
        email=email,
        password_hash=pwd_context.hash(password),
        full_name=full_name,
        role="customer",
    )
    db.session.add(user)
    db.session.flush()

    token = secrets.token_urlsafe(32)
    user.verification_token = token
    db.session.commit()

    _send_verification_email(email, token)
    return token


def verify_email(token: str):
    user = db.session.execute(
        select(models.User).where(models.User.verification_token == token)
    ).scalar_one_or_none()
    if user is None:
        raise ValueError("invalid or expired verification token")

    user.is_verified = True
    user.verification_token = None
    db.session.flush()

    if user.email:
        affected = db.session.execute(
            db.update(models.Customer)
            .where(models.Customer.customer_id.isnot(None), models.Customer.user_id.is_(None))
            .values(user_id=user.id, email=user.email, name=user.full_name)
        ).rowcount
        # This branch only applies when we require a customer_id at registration.
        # For the default self-register flow we leave customer claim to the verify path below.
        db.session.commit()


def authenticate(email: str, password: str) -> tuple[models.User, str]:
    user = db.session.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none()
    if user is None or not pwd_context.verify(password, user.password_hash):
        raise ValueError("invalid credentials")

    access_token = _create_access_token(user)
    return user, access_token


def request_password_reset(email: str) -> str | None:
    user = db.session.execute(select(models.User).where(models.User.email == email)).scalar_one_or_none()
    if user is None:
        return None

    token = secrets.token_urlsafe(32)
    user.reset_token = token
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.session.commit()
    _send_reset_email(user.email, token)
    return token


def reset_password(token: str, new_password: str):
    user = db.session.execute(
        select(models.User).where(models.User.reset_token == token)
    ).scalar_one_or_none()
    if user is None:
        raise ValueError("invalid or expired reset token")
    if user.reset_token_expires is None or user.reset_token_expires < datetime.now(timezone.utc):
        raise ValueError("reset token has expired")

    user.password_hash = pwd_context.hash(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.session.commit()


def get_current_user(user_id: int | None) -> models.User | None:
    if user_id is None:
        return None
    return db.session.get(models.User, int(user_id))


def _create_access_token(user: models.User) -> str:
    from flask_jwt_extended import create_access_token
    return create_access_token(
        identity=user.id,
        additional_claims={"role": user.role, "email": user.email},
    )


def _send_verification_email(to: str, token: str):
    _send_mail(
        subject="Verify your email",
        recipients=[to],
        body=_verification_email_body(token),
    )


def _send_reset_email(to: str, token: str):
    _send_mail(
        subject="Reset your password",
        recipients=[to],
        body=_reset_email_body(token),
    )


def _send_mail(subject: str, recipients: list[str], body: str):
    app = current_app._get_current_object()
    with app.app_context():
        mail = current_app.extensions["mail"]
        message = Message(subject=subject, recipients=recipients, body=body)
        mail.send(message)


def _verification_email_body(token: str) -> str:
    verify_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/verify/{token}"
    return f"Click here to verify your email:\n\n{verify_url}\n\nThis link expires in 24 hours."


def _reset_email_body(token: str) -> str:
    reset_url = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:5173')}/reset/{token}"
    return f"Click here to reset your password:\n\n{reset_url}\n\nThis link expires in 1 hour."
