import logging

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from passlib.context import CryptContext

log = logging.getLogger(__name__)

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()

_bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__ident="2b")


def _bcrypt_digest(secret):
    return _bcrypt.digest(secret)


def _bcrypt_hash(secret):
    return _bcrypt.hash(secret)


def _bcrypt_verify(secret, hash):
    return _bcrypt.verify(secret, hash)

