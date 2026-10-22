"""Server-side pricing: the API must ignore client-supplied unit_price."""


def test_create_order_uses_server_price(client, admin_headers, customer_user, sample_product):
    # sample_product.current_price is 19.99 in the seeded fixture
    payload = {
        "order_id": "ORD9700",
        "order_date": "2026-10-16",
        "customer_id": "C9001",
        "items": [
            {"product_id": sample_product.product_id, "quantity": 2, "unit_price": 0.01}
        ],
    }
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 201, resp.get_json()
    item = resp.get_json()["items"][0]
    assert item["unit_price"] == float(sample_product.current_price)
    assert item["unit_price"] != 0.01


def test_create_order_without_unit_price_succeeds(client, admin_headers, customer_user, sample_product):
    payload = {
        "order_id": "ORD9701",
        "order_date": "2026-10-16",
        "customer_id": "C9001",
        "items": [
            {"product_id": sample_product.product_id, "quantity": 1}
        ],
    }
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 201, resp.get_json()


def test_create_order_honors_server_price_not_client(client, admin_headers, customer_user, sample_product):
    """A wildly inflated client price must not be used."""
    payload = {
        "order_id": "ORD9702",
        "order_date": "2026-10-16",
        "customer_id": "C9001",
        "items": [
            {"product_id": sample_product.product_id, "quantity": 1, "unit_price": 999999.99}
        ],
    }
    resp = client.post("/api/orders", json=payload, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.get_json()["items"][0]["unit_price"] == float(sample_product.current_price)

