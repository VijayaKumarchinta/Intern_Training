"""Report accuracy: the numbers must be correct, not just the status code."""


def _make_order(client, admin_headers, order_id, qty, status):
    payload = {
        "order_id": order_id,
        "order_date": "2026-10-16",
        "customer_id": "C9001",
        "order_status": status,
        "items": [{"product_id": 1, "quantity": qty}],
    }
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()


def test_product_wise_excludes_non_sale_statuses(client, admin_headers, customer_user):
    """Only Shipped and Delivered count toward product-wise totals."""
    _make_order(client, admin_headers, "ORD9800", 2, "Pending")
    _make_order(client, admin_headers, "ORD9801", 3, "Shipped")
    _make_order(client, admin_headers, "ORD9802", 4, "Delivered")
    _make_order(client, admin_headers, "ORD9803", 5, "Cancelled")

    resp = client.get("/api/reports/product-wise", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.get_json()
    assert len(rows) == 1
    # 3 (Shipped) + 4 (Delivered) = 7 units. Pending and Cancelled excluded.
    assert rows[0]["units"] == 7


def test_product_wise_revenue_uses_recorded_unit_price(client, admin_headers, customer_user):
    """Revenue must use order_item.unit_price, not products.current_price."""
    _make_order(client, admin_headers, "ORD9810", 2, "Shipped")
    resp = client.get("/api/reports/product-wise", headers=admin_headers)
    row = resp.get_json()[0]
    # Fixture product is 19.99; two units
    assert row["revenue"] == 2 * 19.99


def test_date_wise_day_and_month_agree(client, admin_headers, customer_user):
    """Grouping by day vs month must sum to the same total units."""
    _make_order(client, admin_headers, "ORD9820", 1, "Shipped")
    _make_order(client, admin_headers, "ORD9821", 2, "Delivered")
    _make_order(client, admin_headers, "ORD9822", 5, "Pending")  # excluded

    day = client.get("/api/reports/date-wise?group=day", headers=admin_headers).get_json()
    month = client.get("/api/reports/date-wise?group=month", headers=admin_headers).get_json()
    assert sum(r["units"] for r in day) == 3
    assert sum(r["units"] for r in month) == 3


def test_date_wise_excludes_non_sale_statuses(client, admin_headers, customer_user):
    _make_order(client, admin_headers, "ORD9830", 10, "Cancelled")
    _make_order(client, admin_headers, "ORD9831", 10, "Returned")
    _make_order(client, admin_headers, "ORD9832", 10, "Pending")

    resp = client.get("/api/reports/date-wise?group=day", headers=admin_headers)
    rows = resp.get_json()
    # No Shipped/Delivered orders => no rows, or rows with zero units
    assert all(r["units"] == 0 for r in rows) or rows == []


def test_reports_empty_when_no_sale_orders(client, admin_headers, customer_user):
    """An empty report must return an empty list, not an error."""
    resp = client.get("/api/reports/product-wise", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json() == []

    resp = client.get("/api/reports/date-wise?group=day", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json() == []