from .db import db

# Singletons initialized via create_app()
# db = SQLAlchemy() - initialized with app in create_app()
# jwt and mail would be initialized similarly in a full implementation

def hash_password(plain: str) -> str:
    """Hash a plain text password using bcrypt."""
    import bcrypt
    if not isinstance(plain, str):
        raise TypeError("password must be a string")
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain text password against a hash."""
    if not plain or not hashed:
        return False
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False