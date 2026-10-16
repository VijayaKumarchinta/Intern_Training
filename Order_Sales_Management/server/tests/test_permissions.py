"""RBAC regression tests.

Locks in the security model verified manually:
- Role comes from DB, not JWT
- Customer cannot access admin-only endpoints
- Customer sees only own orders
- Customer cannot filter by another customer's ID
- Token version bump revokes tokens
- Unauthenticated and malformed requests rejected
"""


def test_health_unauthenticated(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_root_unauthenticated(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_rejects_malformed_token(client):
    resp = client.get("/api/auth/me", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 422


def test_admin_can_access_me(client, admin_headers):
    resp = client.get("/api/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["role"] == "admin"


def test_customer_can_access_me(client, customer_headers):
    resp = client.get("/api/auth/me", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.get_json()["role"] == "customer"


def test_customer_blocked_from_reports_product_wise(client, customer_headers):
    resp = client.get("/api/reports/product-wise", headers=customer_headers)
    assert resp.status_code == 403


def test_customer_blocked_from_reports_date_wise(client, customer_headers):
    resp = client.get("/api/reports/date-wise?group=day", headers=customer_headers)
    assert resp.status_code == 403


def test_customer_blocked_from_duplicates(client, customer_headers):
    resp = client.get("/api/orders/duplicates", headers=customer_headers)
    assert resp.status_code == 403


def test_customer_blocked_from_db_diagnostics(client, customer_headers):
    resp = client.get("/db", headers=customer_headers)
    assert resp.status_code == 403


def test_customer_blocked_from_creating_order(client, customer_headers, sample_product):
    payload = {
        "order_id": "ORD9001",
        "order_date": "2026-10-16",
        "customer_id": "C9001",
        "items": [
            {
                "product_id": sample_product.product_id,
                "quantity": 1,
                "unit_price": 10.0,
            }
        ],
    }
    resp = client.post("/api/orders", json=payload, headers=customer_headers)
    assert resp.status_code == 403


def test_customer_blocked_from_validate_endpoint(client, customer_headers):
    resp = client.post("/api/orders/validate", json={}, headers=customer_headers)
    assert resp.status_code == 403


def test_customer_blocked_from_patching_status(client, customer_headers):
    resp = client.patch(
        "/api/orders/ORD0001/status",
        json={"order_status": "Shipped"},
        headers=customer_headers,
    )
    assert resp.status_code == 403


def test_admin_can_access_reports(client, admin_headers):
    resp = client.get("/api/reports/product-wise", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_admin_can_access_db_diagnostics(client, admin_headers):
    resp = client.get("/db", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert "users" in body and "orders" in body and "customers" in body


def test_admin_can_list_duplicates(client, admin_headers):
    resp = client.get("/api/orders/duplicates", headers=admin_headers)
    assert resp.status_code == 200
    assert "duplicates" in resp.get_json()


def test_customer_listing_orders_sees_empty_when_none(client, customer_headers):
    resp = client.get("/api/orders", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 0
    assert resp.get_json()["orders"] == []


def test_customer_cannot_filter_by_other_customer_id(client, customer_headers):
    resp = client.get("/api/orders?customer_id=C9002", headers=customer_headers)
    assert resp.status_code == 403


def test_customer_can_filter_by_own_customer_id(client, customer_headers):
    resp = client.get("/api/orders?customer_id=C9001", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.get_json()["total"] == 0


def test_customer_cannot_view_other_customers_order(
    client, admin_headers, customer_headers, other_customer_headers, sample_product
):
    order_payload = {
        "order_id": "ORD9100",
        "order_date": "2026-10-16",
        "customer_id": "C9002",
        "order_status": "Pending",
        "items": [
            {
                "product_id": sample_product.product_id,
                "quantity": 1,
                "unit_price": 10.0,
            }
        ],
    }
    created = client.post("/api/orders", json=order_payload, headers=admin_headers)
    assert created.status_code == 201

    resp = client.get("/api/orders/ORD9100", headers=customer_headers)
    assert resp.status_code == 404

    resp = client.get("/api/orders/ORD9100", headers=other_customer_headers)
    assert resp.status_code == 200
    assert resp.get_json()["order_id"] == "ORD9100"


def test_admin_can_view_any_order(
    client, admin_headers, other_customer_headers, sample_product
):
    order_payload = {
        "order_id": "ORD9101",
        "order_date": "2026-10-16",
        "customer_id": "C9002",
        "order_status": "Pending",
        "items": [
            {
                "product_id": sample_product.product_id,
                "quantity": 1,
                "unit_price": 10.0,
            }
        ],
    }
    created = client.post("/api/orders", json=order_payload, headers=admin_headers)
    assert created.status_code == 201

    resp = client.get("/api/orders/ORD9101", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["order_id"] == "ORD9101"


def test_token_version_bump_revokes_token(client, admin_headers, admin_user, app_ctx):
    from app.extensions import db

    ok = client.get("/api/auth/me", headers=admin_headers)
    assert ok.status_code == 200

    admin_user.token_version += 1
    db.session.commit()

    revoked = client.get("/api/auth/me", headers=admin_headers)
    assert revoked.status_code == 401


def test_new_login_after_revocation_works(client, admin_headers, admin_user, app_ctx):
    from app.extensions import db

    admin_user.token_version += 1
    db.session.commit()

    stale = client.get("/api/auth/me", headers=admin_headers)
    assert stale.status_code == 401

    login = client.post(
        "/api/auth/login",
        json={"email": admin_user.email, "password": "AdminPass123!"},
    )
    assert login.status_code == 200
    fresh_token = login.get_json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {fresh_token}"})
    assert me.status_code == 200


def test_role_cannot_be_forged_via_jwt(client, customer_token):
    resp = client.get("/api/reports/product-wise", headers={"Authorization": f"Bearer {customer_token}"})
    assert resp.status_code == 403


def test_other_customer_is_isolated(client, customer_headers, other_customer_headers):
    a = client.get("/api/orders?customer_id=C9001", headers=customer_headers)
    b = client.get("/api/orders?customer_id=C9002", headers=other_customer_headers)
    assert a.status_code == 200
    assert b.status_code == 200

    cross_a = client.get("/api/orders?customer_id=C9002", headers=customer_headers)
    cross_b = client.get("/api/orders?customer_id=C9001", headers=other_customer_headers)
    assert cross_a.status_code == 403
    assert cross_b.status_code == 403

def test_deleted_user_token_returns_401(client, admin_headers, admin_user, app_ctx):
    """A token for a user that no longer exists must not reveal that fact."""
    from app.extensions import db

    ok = client.get("/api/auth/me", headers=admin_headers)
    assert ok.status_code == 200

    db.session.delete(admin_user)
    db.session.commit()

    resp = client.get("/api/auth/me", headers=admin_headers)
    assert resp.status_code == 401
