from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from passlib.context import CryptContext

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()

bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto")