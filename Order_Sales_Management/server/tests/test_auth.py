"""Auth lifecycle tests (register -> verify -> login -> reset) plus the
loyalty-card ownership security model:

    - Registration with a customer_id requires matching email.
    - The link only happens after OTP verification succeeds.
    - Customers with no email on file cannot be self-claimed.
"""

import pytest


@pytest.fixture
def capture_verification(monkeypatch):
    captured = {}

    def fake_send(email, code):
        captured["email"] = email
        captured["code"] = code

    monkeypatch.setattr(
        "app.services.auth_service.send_verification_code",
        fake_send,
    )
    return captured


@pytest.fixture
def capture_reset(monkeypatch):
    captured = {}

    def fake_send(email, token):
        captured["email"] = email
        captured["token"] = token

    monkeypatch.setattr(
        "app.services.auth_service.send_password_reset",
        fake_send,
    )
    return captured


def _register_payload(email="new@test.local", customer_id=None, password="NewPass123!"):
    p = {
        "email": email,
        "password": password,
        "full_name": "New User",
    }
    if customer_id is not None:
        p["customer_id"] = customer_id
    return p


def _seed_customer(customer_id, email, name="Test Customer"):
    from app.extensions import db
    from app.models import Customer

    cust = Customer(customer_id=customer_id, cust_name=name, email=email)
    db.session.add(cust)
    db.session.commit()
    return cust


# --- Registration ---


def test_register_new_user_returns_201(client, capture_verification, app_ctx):
    resp = client.post("/api/auth/register", json=_register_payload())
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["email"] == "new@test.local"
    assert body["is_verified"] is False
    assert "code" in capture_verification
    assert len(capture_verification["code"]) == 6


def test_register_duplicate_email_returns_400(client, capture_verification, app_ctx):
    first = client.post("/api/auth/register", json=_register_payload(email="dup@test.local"))
    assert first.status_code == 201
    second = client.post("/api/auth/register", json=_register_payload(email="dup@test.local"))
    assert second.status_code == 400
    assert "already registered" in second.get_json()["error"].lower()


def test_register_invalid_email_returns_400(client):
    resp = client.post("/api/auth/register", json=_register_payload(email="not-an-email"))
    assert resp.status_code == 400


def test_register_short_password_returns_400(client, app_ctx):
    resp = client.post(
        "/api/auth/register",
        json=_register_payload(password="short"),
    )
    assert resp.status_code == 400
    assert "8 characters" in resp.get_json()["error"]


def test_register_password_too_long_returns_400(client, app_ctx):
    resp = client.post(
        "/api/auth/register",
        json=_register_payload(password="a" * 100),
    )
    assert resp.status_code == 400


# --- Loyalty-card: registration with customer_id ---


def test_register_with_valid_customer_id_succeeds(client, capture_verification, app_ctx):
    """Happy path: customer exists, has email, and emails match."""
    _seed_customer("C9100", "loyal@test.local")
    resp = client.post(
        "/api/auth/register",
        json=_register_payload(email="loyal@test.local", customer_id="C9100"),
    )
    assert resp.status_code == 201, resp.get_json()


def test_register_unknown_customer_id_returns_400(client):
    resp = client.post(
        "/api/auth/register",
        json=_register_payload(email="x@test.local", customer_id="C9999"),
    )
    assert resp.status_code == 400
    assert "customer" in resp.get_json()["error"].lower()


def test_register_customer_email_mismatch_returns_400(client, app_ctx):
    """Attacker tries to claim a customer with a different email -> reject."""
    _seed_customer("C9105", "owner@test.local")
    resp = client.post(
        "/api/auth/register",
        json=_register_payload(email="attacker@test.local", customer_id="C9105"),
    )
    assert resp.status_code == 400
    assert "does not match" in resp.get_json()["error"].lower()


def test_register_customer_without_email_returns_400(client, app_ctx):
    """Imported customer with NULL email cannot be self-claimed."""
    _seed_customer("C9106", None)
    resp = client.post(
        "/api/auth/register",
        json=_register_payload(email="someone@test.local", customer_id="C9106"),
    )
    assert resp.status_code == 400
    assert "no email" in resp.get_json()["error"].lower()


def test_register_customer_already_linked_returns_400(
    client, capture_verification, app_ctx
):
    _seed_customer("C9107", "one@test.local")
    first = client.post(
        "/api/auth/register",
        json=_register_payload(email="one@test.local", customer_id="C9107"),
    )
    assert first.status_code == 201
    code = capture_verification["code"]
    assert client.post(
        "/api/auth/verify",
        json={"email": "one@test.local", "code": code, "customer_id": "C9107"},
    ).status_code == 200

    # Second account tries to claim the same customer -> reject.
    resp = client.post(
        "/api/auth/register",
        json=_register_payload(email="two@test.local", customer_id="C9107"),
    )
    assert resp.status_code == 400
    assert "already linked" in resp.get_json()["error"].lower()


# --- Verification ---


def test_verify_correct_code_succeeds(client, capture_verification, app_ctx):
    _seed_customer("C9200", "verify@test.local")
    client.post(
        "/api/auth/register",
        json=_register_payload(email="verify@test.local", customer_id="C9200"),
    )
    code = capture_verification["code"]

    resp = client.post(
        "/api/auth/verify",
        json={"email": "verify@test.local", "code": code, "customer_id": "C9200"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["is_verified"] is True

    # And the link is now active
    from app.extensions import db
    from app.models import Customer
    cust = db.session.get(Customer, "C9200")
    assert cust.user_id is not None


def test_verify_without_customer_id_links_nothing(client, capture_verification, app_ctx):
    """Registering without a customer_id is fine — just no linking."""
    client.post("/api/auth/register", json=_register_payload(email="nolink@test.local"))
    code = capture_verification["code"]

    resp = client.post(
        "/api/auth/verify",
        json={"email": "nolink@test.local", "code": code},
    )
    assert resp.status_code == 200


def test_verify_wrong_code_returns_400_and_decrements_attempts(
    client, capture_verification, app_ctx
):
    _seed_customer("C9201", "wrong@test.local")
    client.post(
        "/api/auth/register",
        json=_register_payload(email="wrong@test.local", customer_id="C9201"),
    )
    resp = client.post(
        "/api/auth/verify",
        json={"email": "wrong@test.local", "code": "000000"},
    )
    assert resp.status_code == 400
    assert "attempts remaining" in resp.get_json()["error"]


def test_verify_too_many_attempts_returns_400(client, capture_verification, app_ctx):
    _seed_customer("C9202", "many@test.local")
    client.post(
        "/api/auth/register",
        json=_register_payload(email="many@test.local", customer_id="C9202"),
    )
    for _ in range(3):
        assert client.post(
            "/api/auth/verify",
            json={"email": "many@test.local", "code": "000000"},
        ).status_code == 400

    final = client.post(
        "/api/auth/verify",
        json={"email": "many@test.local", "code": "000000"},
    )
    assert final.status_code == 400
    assert "too many" in final.get_json()["error"].lower()


def test_verify_unknown_email_returns_invalid_code(client):
    resp = client.post(
        "/api/auth/verify",
        json={"email": "nobody@test.local", "code": "123456"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Invalid code"


def test_verify_missing_fields_returns_400(client):
    resp = client.post("/api/auth/verify", json={})
    assert resp.status_code == 400


def test_verify_after_verified_returns_400(client, capture_verification, app_ctx):
    _seed_customer("C9203", "again@test.local")
    client.post(
        "/api/auth/register",
        json=_register_payload(email="again@test.local", customer_id="C9203"),
    )
    code = capture_verification["code"]
    assert client.post(
        "/api/auth/verify",
        json={"email": "again@test.local", "code": code},
    ).status_code == 200

    again = client.post(
        "/api/auth/verify",
        json={"email": "again@test.local", "code": code},
    )
    assert again.status_code == 400
    assert "already verified" in again.get_json()["error"].lower()


# --- Resend ---


def test_resend_verification_returns_200_even_for_unknown(client):
    resp = client.post(
        "/api/auth/resend-verification",
        json={"email": "nobody@test.local"},
    )
    assert resp.status_code == 200


def test_resend_verification_generates_new_code(
    client, capture_verification, app_ctx
):
    client.post("/api/auth/register", json=_register_payload(email="resend@test.local"))
    first = capture_verification["code"]
    client.post(
        "/api/auth/resend-verification",
        json={"email": "resend@test.local"},
    )
    second = capture_verification["code"]
    assert first != second


# --- Login ---


def test_login_before_verification_returns_401(client, capture_verification, app_ctx):
    client.post(
        "/api/auth/register",
        json=_register_payload(email="unverified@test.local", password="ValidPass123!"),
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "unverified@test.local", "password": "ValidPass123!"},
    )
    assert resp.status_code == 401
    assert "verify" in resp.get_json()["error"].lower()


def test_login_with_wrong_password_returns_401(client, app_ctx):
    from app.extensions import db, hash_password
    from app.models import User

    user = User(
        email="loginwrong@test.local",
        password_hash=hash_password("CorrectPass123!"),
        full_name="Test",
        role="customer",
        is_verified=True,
    )
    db.session.add(user)
    db.session.commit()

    resp = client.post(
        "/api/auth/login",
        json={"email": "loginwrong@test.local", "password": "WrongPass123!"},
    )
    assert resp.status_code == 401
    assert resp.get_json()["error"] == "Invalid credentials"


def test_login_unknown_email_returns_401(client):
    resp = client.post(
        "/api/auth/login",
        json={"email": "nobody@test.local", "password": "Anything123!"},
    )
    assert resp.status_code == 401


def test_login_returns_valid_jwt(client, capture_verification, app_ctx):
    client.post(
        "/api/auth/register",
        json=_register_payload(email="validlogin@test.local", password="ValidPass123!"),
    )
    code = capture_verification["code"]
    client.post(
        "/api/auth/verify",
        json={"email": "validlogin@test.local", "code": code},
    )
    resp = client.post(
        "/api/auth/login",
        json={"email": "validlogin@test.local", "password": "ValidPass123!"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert "access_token" in body
    assert body["user"]["email"] == "validlogin@test.local"
    assert body["user"]["role"] == "customer"


# --- Forgot / Reset password ---


def test_forgot_password_returns_200_even_for_unknown(client):
    resp = client.post(
        "/api/auth/forgot-password",
        json={"email": "nobody@test.local"},
    )
    assert resp.status_code == 200


def test_forgot_password_sends_token(client, capture_reset, app_ctx):
    from app.extensions import db, hash_password
    from app.models import User

    user = User(
        email="forgot@test.local",
        password_hash=hash_password("OldPass123!"),
        full_name="Forgot",
        role="customer",
        is_verified=True,
    )
    db.session.add(user)
    db.session.commit()

    resp = client.post(
        "/api/auth/forgot-password",
        json={"email": "forgot@test.local"},
    )
    assert resp.status_code == 200
    assert "token" in capture_reset
    assert len(capture_reset["token"]) > 20


def test_reset_password_with_valid_token_succeeds(client, capture_reset, app_ctx):
    from app.extensions import db, hash_password
    from app.models import User

    user = User(
        email="reset@test.local",
        password_hash=hash_password("OldPass123!"),
        full_name="Reset",
        role="customer",
        is_verified=True,
    )
    db.session.add(user)
    db.session.commit()
    old_tv = user.token_version

    client.post(
        "/api/auth/forgot-password",
        json={"email": "reset@test.local"},
    )
    token = capture_reset["token"]

    resp = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "NewPass123!"},
    )
    assert resp.status_code == 200

    fresh = db.session.get(User, user.id)
    assert fresh.token_version == old_tv + 1

    login = client.post(
        "/api/auth/login",
        json={"email": "reset@test.local", "password": "NewPass123!"},
    )
    assert login.status_code == 200


def test_reset_password_with_invalid_token_returns_400(client):
    resp = client.post(
        "/api/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": "NewPass123!"},
    )
    assert resp.status_code == 400


def test_reset_password_with_short_password_returns_400(client, capture_reset, app_ctx):
    from app.extensions import db, hash_password
    from app.models import User

    user = User(
        email="shortreset@test.local",
        password_hash=hash_password("OldPass123!"),
        full_name="Short",
        role="customer",
        is_verified=True,
    )
    db.session.add(user)
    db.session.commit()

    client.post(
        "/api/auth/forgot-password",
        json={"email": "shortreset@test.local"},
    )
    token = capture_reset["token"]

    resp = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "short"},
    )
    assert resp.status_code == 400


def test_reset_password_token_used_twice_returns_400(
    client, capture_reset, app_ctx
):
    from app.extensions import db, hash_password
    from app.models import User

    user = User(
        email="twice@test.local",
        password_hash=hash_password("OldPass123!"),
        full_name="Twice",
        role="customer",
        is_verified=True,
    )
    db.session.add(user)
    db.session.commit()

    client.post(
        "/api/auth/forgot-password",
        json={"email": "twice@test.local"},
    )
    token = capture_reset["token"]

    first = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "NewPass123!"},
    )
    assert first.status_code == 200

    second = client.post(
        "/api/auth/reset-password",
        json={"token": token, "new_password": "Another123!"},
    )
    assert second.status_code == 400