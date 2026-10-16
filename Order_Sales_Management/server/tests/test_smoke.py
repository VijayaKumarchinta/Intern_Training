def test_fixtures_load(client, admin_headers, customer_headers, sample_product):
    # Just prove the plumbing works
    assert client is not None
    assert "Authorization" in admin_headers
    assert "Authorization" in customer_headers
    assert sample_product is not None
    assert sample_product.product_id >= 1


def test_app_uses_test_db(app):
    with app.app_context():
        from app.extensions import db
        from sqlalchemy import text
        db_name = db.session.execute(text("SELECT current_database()")).scalar()
        assert db_name == "machine_sensor_test_db", f"Expected test DB, got {db_name}"
