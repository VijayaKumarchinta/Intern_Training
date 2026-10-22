"""Order workflow tests.

Covers: create, validate, status transitions, duplicates, ownership filters.
"""

import pytest


def _order_payload(
    order_id="ORD9600",
    customer_id="C9001",
    order_date="2026-10-16",
    items=None,
    status="Pending",
):
    if items is None:
        items = [{"product_id": 1, "quantity": 1, "unit_price": 10.0}]
    return {
        "order_id": order_id,
        "order_date": order_date,
        "customer_id": customer_id,
        "order_status": status,
        "items": items,
    }


# --- Create ---


def test_create_order_as_admin_succeeds(
    client, admin_headers, customer_user, sample_product
):
    payload = _order_payload(
        items=[
            {
                "product_id": sample_product.product_id,
                "quantity": 3,
                "unit_price": 20.0,
            }
        ]
    )
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["order_id"] == "ORD9600"
    assert body["order_status"] == "Pending"
    assert body["customer_id"] == "C9001"
    assert body["items"][0]["unit_price"] == float(sample_product.current_price)
    assert body["total"] == 3 * float(sample_product.current_price)

def test_create_order_duplicate_returns_409(client, admin_headers, sample_order):
    duplicate = _order_payload(
        order_id="ORD9500",
        items=[{"product_id": 1, "quantity": 1, "unit_price": 10.0}],
    )
    resp = client.post("/api/orders", json=duplicate, headers=admin_headers)
    assert resp.status_code == 409


def test_create_order_invalid_order_id_format(client, admin_headers, customer_user):
    payload = _order_payload(order_id="BAD-ID")
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 400
    errors = resp.get_json().get("errors") or [resp.get_json().get("error")]
    assert any("ORD####" in str(e) for e in errors)


def test_create_order_invalid_date_format(client, admin_headers, customer_user):
    payload = _order_payload(order_date="10-16-2026")
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 400


def test_create_order_unknown_customer(client, admin_headers, sample_product):
    payload = _order_payload(
        customer_id="C0000",
        items=[
            {
                "product_id": sample_product.product_id,
                "quantity": 1,
                "unit_price": 10.0,
            }
        ],
    )
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 400


def test_create_order_unknown_product(client, admin_headers, customer_user):
    payload = _order_payload(
        items=[{"product_id": 999999, "quantity": 1, "unit_price": 10.0}]
    )
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 400


def test_create_order_no_items_returns_400(client, admin_headers, customer_user):
    payload = _order_payload(items=[])
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 400


def test_create_order_duplicate_product_in_items(
    client, admin_headers, customer_user, sample_product
):
    payload = _order_payload(
        items=[
            {"product_id": sample_product.product_id, "quantity": 1, "unit_price": 5.0},
            {"product_id": sample_product.product_id, "quantity": 2, "unit_price": 5.0},
        ]
    )
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 400


def test_create_order_quantity_bounds_low(
    client, admin_headers, customer_user, sample_product
):
    payload = _order_payload(
        items=[
            {"product_id": sample_product.product_id, "quantity": 0, "unit_price": 5.0}
        ]
    )
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 400


def test_create_order_quantity_bounds_high(
    client, admin_headers, customer_user, sample_product
):
    payload = _order_payload(
        items=[
            {
                "product_id": sample_product.product_id,
                "quantity": 1001,
                "unit_price": 5.0,
            }
        ]
    )
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 400


def test_create_order_ignores_negative_client_price(
    client, admin_headers, customer_user, sample_product
):
    payload = _order_payload(
        items=[
            {
                "product_id": sample_product.product_id,
                "quantity": 1,
                "unit_price": -1.0,
            }
        ]
    )
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 201
    item = resp.get_json()["items"][0]
    assert item["unit_price"] == float(sample_product.current_price)

def test_status_transition_valid_flow(client, admin_headers, sample_order):
    """Pending -> Received -> Shipped -> Delivered."""
    for next_status in ("Received", "Shipped", "Delivered"):
        resp = client.patch(
            "/api/orders/ORD9500/status",
            json={"order_status": next_status},
            headers=admin_headers,
        )
        assert resp.status_code == 200, f"{next_status}: {resp.get_json()}"
        assert resp.get_json()["order_status"] == next_status


def test_status_transition_invalid_returns_400(client, admin_headers, sample_order):
    """Pending -> Delivered is not allowed."""
    resp = client.patch(
        "/api/orders/ORD9500/status",
        json={"order_status": "Delivered"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_status_transition_terminal_states_locked(
    client, admin_headers, sample_order
):
    """After Shipped -> Returned, no further transitions allowed."""
    client.patch(
        "/api/orders/ORD9500/status",
        json={"order_status": "Shipped"},
        headers=admin_headers,
    )
    client.patch(
        "/api/orders/ORD9500/status",
        json={"order_status": "Returned"},
        headers=admin_headers,
    )
    resp = client.patch(
        "/api/orders/ORD9500/status",
        json={"order_status": "Shipped"},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_status_transition_missing_field(client, admin_headers, sample_order):
    resp = client.patch(
        "/api/orders/ORD9500/status",
        json={},
        headers=admin_headers,
    )
    assert resp.status_code == 400


def test_status_transition_unknown_order(client, admin_headers):
    resp = client.patch(
        "/api/orders/ORD9999/status",
        json={"order_status": "Received"},
        headers=admin_headers,
    )
    assert resp.status_code == 404


# --- List / pagination ---


def test_list_orders_admin_sees_all(
    client, admin_headers, sample_order, other_customer_order
):
    resp = client.get("/api/orders", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total"] >= 2
    order_ids = {o["order_id"] for o in body["orders"]}
    assert "ORD9500" in order_ids
    assert "ORD9501" in order_ids


def test_list_orders_customer_sees_only_own(
    client, customer_headers, sample_order, other_customer_order
):
    resp = client.get("/api/orders", headers=customer_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    for o in body["orders"]:
        assert o["customer_id"] == "C9001"


def test_list_orders_pagination(client, admin_headers, customer_user, sample_product):
    for i in range(5):
        payload = _order_payload(
            order_id=f"ORD97{i:02d}",
            items=[
                {
                    "product_id": sample_product.product_id,
                    "quantity": 1,
                    "unit_price": 5.0,
                }
            ],
        )
        client.post("/api/orders", json=payload, headers=admin_headers)

    resp = client.get("/api/orders?page=1&per_page=2", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["orders"]) == 2
    assert body["per_page"] == 2
    assert body["total"] >= 5


def test_list_orders_filter_by_status(
    client, admin_headers, sample_order, customer_user, sample_product
):
    other = _order_payload(
        order_id="ORD9601",
        items=[
            {
                "product_id": sample_product.product_id,
                "quantity": 1,
                "unit_price": 10.0,
            }
        ],
        status="Received",
    )
    client.post("/api/orders", json=other, headers=admin_headers)

    resp = client.get("/api/orders?status=Received", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    for o in body["orders"]:
        assert o["order_status"] == "Received"


# --- Duplicates ---


def test_duplicates_endpoint_detects_repeats(
    client, admin_headers, customer_user, sample_product
):
    """Two orders with identical (customer, product, qty, price, date)."""
    items = [
        {
            "product_id": sample_product.product_id,
            "quantity": 5,
            "unit_price": 15.0,
        }
    ]
    first = _order_payload(order_id="ORD9800", items=items)
    second = _order_payload(order_id="ORD9801", items=items)

    assert client.post("/api/orders", json=first, headers=admin_headers).status_code == 201
    assert client.post("/api/orders", json=second, headers=admin_headers).status_code == 201

    resp = client.get("/api/orders/duplicates", headers=admin_headers)
    assert resp.status_code == 200
    dupes = resp.get_json()["duplicates"]
    assert any(
        set(d["order_ids"]) >= {"ORD9800", "ORD9801"} for d in dupes
    )


def test_duplicates_empty_when_no_repeats(client, admin_headers, sample_order):
    resp = client.get("/api/orders/duplicates", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()["duplicates"] == []

def test_list_orders_invalid_status_returns_400(client, admin_headers):
    resp = client.get("/api/orders?status=Garbage", headers=admin_headers)
    assert resp.status_code == 400
    assert "Invalid status" in resp.get_json()["error"]


def test_list_orders_valid_status_returns_200(client, admin_headers):
    resp = client.get("/api/orders?status=Pending", headers=admin_headers)
    assert resp.status_code == 200
