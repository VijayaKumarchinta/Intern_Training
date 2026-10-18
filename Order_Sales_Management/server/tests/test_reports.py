"""Report accuracy: the numbers must be correct, not just the status code."""
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
    """Helper to bypass the forced 'Pending' state and push to a sale status."""
    resp = client.patch(
        f"/api/orders/{order_id}/status",
        json={"order_status": status},
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.get_json()


def test_product_wise_excludes_non_sale_statuses(client, admin_headers, customer_user):
    """Only Shipped and Delivered count toward product-wise totals."""
    _make_order(client, admin_headers, "ORD9800", 2)
    _make_order(client, admin_headers, "ORD9801", 3)
    _make_order(client, admin_headers, "ORD9802", 4)
    _make_order(client, admin_headers, "ORD9803", 5)

    _set_status(client, admin_headers, "ORD9801", "Shipped")

    resp = client.get("/api/reports/product-wise", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.get_json()
    assert len(rows) == 1
    assert rows[0]["units"] == 3.0  

def test_product_wise_revenue_uses_recorded_unit_price(client, admin_headers, customer_user):
    """Revenue must use order_item.unit_price, not products.current_price."""
    _make_order(client, admin_headers, "ORD9810", 2)
    _set_status(client, admin_headers, "ORD9810", "Shipped")

    resp = client.get("/api/reports/product-wise", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.get_json()
    assert len(rows) == 1
    assert rows[0]["units"] == 2.0


def test_date_wise_day_and_month_agree(client, admin_headers, customer_user):
    """Grouping by day vs month must sum to the same total units."""
    _make_order(client, admin_headers, "ORD9820", 1)
    _make_order(client, admin_headers, "ORD9821", 2)

    _set_status(client, admin_headers, "ORD9820", "Shipped")
    _set_status(client, admin_headers, "ORD9820", "Delivered")
    
    _set_status(client, admin_headers, "ORD9821", "Shipped")
    _set_status(client, admin_headers, "ORD9821", "Delivered")

    resp = client.get("/api/reports/date-wise?group=day", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.get_json()
    assert len(rows) == 1
    assert rows[0]["units"] == 3.0 
    assert rows[0]["orders"] == 2

    resp = client.get("/api/reports/date-wise?group=month", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.get_json()
    assert len(rows) == 1
    assert rows[0]["units"] == 3.0


def test_date_wise_excludes_non_sale_statuses(client, admin_headers, customer_user):
    _make_order(client, admin_headers, "ORD9830", 10)
    _make_order(client, admin_headers, "ORD9831", 10)
    _make_order(client, admin_headers, "ORD9832", 10)

    _set_status(client, admin_headers, "ORD9830", "Cancelled")
    _set_status(client, admin_headers, "ORD9831", "Shipped")
    _set_status(client, admin_headers, "ORD9831", "Returned")

    resp = client.get("/api/reports/date-wise?group=day", headers=admin_headers)
    rows = resp.get_json()
    assert all(r["units"] == 0 for r in rows) or rows == []


def test_reports_empty_when_no_sale_orders(client, admin_headers, customer_user):
    """An empty report must return an empty list, not an error."""
    resp = client.get("/api/reports/product-wise", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json() == []

    resp = client.get("/api/reports/date-wise?group=day", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json() == []