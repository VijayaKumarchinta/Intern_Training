import os
import sys
from pathlib import Path

# Force test env BEFORE importing app
os.environ["FLASK_ENV"] = "test"

# Ensure the server/ directory is on sys.path for `from app import ...`
TESTS_DIR = Path(__file__).resolve().parent
SERVER_DIR = TESTS_DIR.parent
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

import pytest
from sqlalchemy import text

from app import create_app
from app.constants import Role
from app.extensions import db as _db
from app.extensions import hash_password
from app.models import Customer, Product, User


@pytest.fixture(scope="session")
def app():
    app = create_app()
    app.config.update(TESTING=True)
    yield app


@pytest.fixture(scope="session")
def app_ctx(app):
    ctx = app.app_context()
    ctx.push()
    yield ctx
    ctx.pop()


@pytest.fixture(scope="session", autouse=True)
def seed_products(app_ctx):
    """Seed static product catalog once per session."""
    existing = _db.session.query(Product).count()
    if existing == 0:
        _db.session.add_all([
            Product(pro_name="Test Product A", current_price=19.99),
            Product(pro_name="Test Product B", current_price=49.99),
            Product(pro_name="Test Product C", current_price=99.99),
        ])
        _db.session.commit()
    yield


@pytest.fixture(autouse=True)
def clean_db(app_ctx):
    """Wipe transactional tables before each test. Products are preserved."""
    _db.session.remove()
    _db.session.execute(text(
        "TRUNCATE order_sales.order_items, order_sales.orders, "
        "order_sales.customers, order_sales.users RESTART IDENTITY CASCADE"
    ))
    _db.session.commit()
    _db.session.remove()
    yield
    _db.session.rollback()
    _db.session.remove()


@pytest.fixture
def client(app):
    return app.test_client()


def _make_user(email, password, role, full_name=None, is_verified=True, customer_id=None):
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name or email.split("@")[0],
        role=role,
        is_verified=is_verified,
    )
    _db.session.add(user)
    _db.session.flush()

    if customer_id is not None:
        cust = Customer(
            customer_id=customer_id,
            user_id=user.id,
            cust_name=user.full_name,
            email=user.email,
        )
        _db.session.add(cust)

    _db.session.commit()
    return user


def _login(client, email, password):
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, f"login failed: {resp.get_json()}"
    return resp.get_json()["access_token"]


@pytest.fixture
def admin_user(app_ctx):
    return _make_user(
        email="admin@test.local",
        password="AdminPass123!",
        role=Role.ADMIN.value,
        full_name="Test Admin",
    )


@pytest.fixture
def admin_token(client, admin_user):
    return _login(client, admin_user.email, "AdminPass123!")


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def customer_user(app_ctx):
    return _make_user(
        email="cust@test.local",
        password="CustPass123!",
        role=Role.CUSTOMER.value,
        full_name="Test Customer",
        customer_id="C9001",
    )


@pytest.fixture
def customer_token(client, customer_user):
    return _login(client, customer_user.email, "CustPass123!")


@pytest.fixture
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}


@pytest.fixture
def other_customer(app_ctx):
    """A second customer, used for cross-tenant access tests."""
    return _make_user(
        email="other@test.local",
        password="OtherPass123!",
        role=Role.CUSTOMER.value,
        full_name="Other Customer",
        customer_id="C9002",
    )


@pytest.fixture
def other_customer_headers(client, other_customer):
    token = _login(client, other_customer.email, "OtherPass123!")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_product(app_ctx):
    return _db.session.query(Product).first()
