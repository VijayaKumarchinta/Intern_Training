"""Report accuracy: verify the summary endpoint returns correct aggregated data."""
from app.extensions import db
from app.models import Order


def _make_order(client, admin_headers, order_id, qty, status="Pending"):
    payload = {
        "order_id": order_id,
        "order_date": "2026-10-16",
        "customer_id": "C9001",
        "items": [{"product_id": 1, "quantity": qty}],
    }
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def _set_status(client, admin_headers, order_id, status):
    resp = client.patch(
        f"/api/orders/{order_id}/status",
        json={"order_status": status},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.get_json()


def test_summary_excludes_non_sale_statuses(client, admin_headers, customer_user):
    """Only Shipped and Delivered count toward revenue."""
    _make_order(client, admin_headers, "ORD9800", 2)
    _make_order(client, admin_headers, "ORD9801", 3)

    _set_status(client, admin_headers, "ORD9801", "Shipped")

    resp = client.get("/api/reports/summary", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()

    # Only ORD9801 (3 units) should count
    assert body["units_sold"] == 3
    assert body["sales_orders"] == 1
    assert body["product_breakdown"][0]["units"] == 3.0


def test_summary_contains_all_sections(client, admin_headers, customer_user):
    """Verify the payload includes KPIs, latest orders, duplicates, and charts."""
    _make_order(client, admin_headers, "ORD9810", 2)
    _set_status(client, admin_headers, "ORD9810", "Shipped")

    resp = client.get("/api/reports/summary", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()

    # KPIs
    assert "revenue" in body
    assert "sales_orders" in body
    assert "units_sold" in body
    assert "awaiting_action" in body

    # Data sections
    assert "latest_orders" in body
    assert "duplicate_groups" in body
    assert "product_breakdown" in body
    assert "monthly_breakdown" in body


def test_summary_empty_state(client, admin_headers):
    """An empty DB should return zeros and empty arrays, not errors."""
    resp = client.get("/api/reports/summary", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["revenue"] == 0.0
    assert body["sales_orders"] == 0
    assert body["product_breakdown"] == []
    assert body["monthly_breakdown"] == []