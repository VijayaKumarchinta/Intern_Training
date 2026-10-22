def normalize_email(email):
    return (email or "").strip().lower()

def validate_password(password):
    if not password or len(password) < 8:
        return "Password must be at least 8 characters"
    if len(password.encode("utf-8")) > 72:
        return "Password must be at most 72 bytes"
    return None

def validate_email(email):
    if not email or "@" not in email:
        return "Invalid email"
    return None
