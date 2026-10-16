import logging
import os
from datetime import datetime, timezone
from flask import current_app

log = logging.getLogger(__name__)

DEV_EMAIL_LOG = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "dev_emails.log")
)

def _write_dev_email_log(kind, email, payload):
    with open(DEV_EMAIL_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()} | {kind} | {email} | {payload}\n")

def send_verification_code(email, code):
    ttl = current_app.config.get("VERIFY_TTL_MINUTES", 2)
    payload = f"Code: {code} (valid {ttl} minutes)"
    _write_dev_email_log("VERIFY-OTP", email, payload)
    log.info("[VERIFY-OTP] To: %s | %s", email, payload)

def send_password_reset(email, token):
    base = current_app.config.get("FRONTEND_URL", "http://localhost:5173")
    link = f"{base}/reset-password?token={token}"
    payload = f"Reset link: {link}"
    _write_dev_email_log("RESET-LINK", email, payload)
    log.info("[RESET-LINK] To: %s | %s", email, payload)