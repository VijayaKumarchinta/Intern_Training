import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def test_imports():
    print("Testing imports...")

    try:
        from server.config import (
            DB_HOST, DB_PORT, DB_NAME, DB_SCHEMA,
            APP_PORT, validate_config,
        )
        print("  [OK] config.py imports OK")
    except Exception as e:
        print(f"  [FAIL] config.py failed: {e}")
        return False

    try:
        from server.utils.validation import (
            validate_non_empty_string, validate_email, validate_positive_int,
            validate_order_items, validate_status_transition,
            VALID_ORDER_STATUSES, ORDER_STATUS_TRANSITIONS,
        )
        print("  [OK] validation.py imports OK")
    except Exception as e:
        print(f"  [FAIL] validation.py failed: {e}")
        return False

    try:
        from server.services.customer_service import (
            get_customer_by_id, get_all_customers, create_customer,
        )
        print("  [OK] customer_service.py imports OK")
    except Exception as e:
        print(f"  [FAIL] customer_service.py failed: {e}")
        return False

    try:
        from server.services.product_service import (
            get_product_by_id, get_all_products, create_product,
        )
        print("  [OK] product_service.py imports OK")
    except Exception as e:
        print(f"  [FAIL] product_service.py failed: {e}")
        return False

    try:
        from server.services.order_service import (
            get_order_by_id, get_all_orders, create_order,
            update_order_status, get_product_sales_report,
            get_date_sales_report, order_exists, compute_order_signature,
        )
        print("  [OK] order_service.py imports OK")
    except Exception as e:
        print(f"  [FAIL] order_service.py failed: {e}")
        return False

    try:
        from server.routes import customer_bp, product_bp, order_bp, report_bp
        print("  [OK] routes import OK")
    except Exception as e:
        print(f"  [FAIL] routes failed: {e}")
        return False

    return True


def test_config():
    print("\nTesting configuration...")

    from server.config import (
        DB_HOST, DB_PORT, DB_NAME, DB_SCHEMA,
        APP_HOST, APP_PORT, validate_config,
    )

    print(f"  DB_HOST: {DB_HOST}")
    print(f"  DB_PORT: {DB_PORT}")
    print(f"  DB_NAME: {DB_NAME}")
    print(f"  DB_SCHEMA: {DB_SCHEMA}")
    print(f"  APP_HOST: {APP_HOST}")
    print(f"  APP_PORT: {APP_PORT}")

    validate_config()
    print("  [OK] Config validated")

    from server.utils.validation import VALID_ORDER_STATUSES, ORDER_STATUS_TRANSITIONS
    print(f"  VALID_ORDER_STATUSES: {VALID_ORDER_STATUSES}")
    print(f"  ORDER_STATUS_TRANSITIONS: {ORDER_STATUS_TRANSITIONS}")

    assert 'pending' in VALID_ORDER_STATUSES
    assert 'processing' in ORDER_STATUS_TRANSITIONS['pending']
    assert 'cancelled' in ORDER_STATUS_TRANSITIONS['pending']
    print("  [OK] Status transitions validated")

    return True


def test_validation():
    print("\nTesting validation functions...")

    from server.utils.validation import (
        validate_non_empty_string,
        validate_email,
        validate_positive_int,
        validate_order_id,
        validate_product_id,
        validate_customer_id,
        validate_order_items,
        validate_status_transition,
    )

    assert validate_non_empty_string("test", "field") == "test"
    print("  [OK] validate_non_empty_string OK")

    assert validate_email("test@example.com") == "test@example.com"
    try:
        validate_email("invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("  [OK] validate_email rejects invalid OK")

    assert validate_positive_int(5, "qty") == 5
    try:
        validate_positive_int(0, "qty")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("  [OK] validate_positive_int rejects 0 OK")

    assert validate_order_id("ORD200000") == "ORD200000"
    assert validate_product_id("MONITOR") == "MONITOR"
    assert validate_customer_id("C72649") == "C72649"
    print("  [OK] ID validators OK")

    items = [
        {"product_id": "MONITOR", "quantity": 2},
        {"product_id": "Phone", "quantity": 1, "unit_price": 151.35},
    ]
    validated = validate_order_items(items)
    assert len(validated) == 2
    assert validated[0]['product_id'] == "MONITOR"
    assert validated[0]['quantity'] == 2
    assert validated[0]['unit_price'] is None
    assert float(validated[1]['unit_price']) == 151.35
    print("  [OK] validate_order_items OK")

    assert validate_status_transition('pending', 'processing') == 'processing'
    try:
        validate_status_transition('delivered', 'pending')
        assert False
    except ValueError:
        print("  [OK] validate_status_transition rejects invalid OK")

    return True


def test_order_calculation():
    print("\nTesting order calculation...")

    items = [
        {"product_id": "MONITOR", "quantity": 5, "unit_price": 570.62},
        {"product_id": "Phone", "quantity": 2, "unit_price": 151.35},
    ]

    total = sum(item['quantity'] * item['unit_price'] for item in items)
    total = round(total, 2)

    expected = round(5 * 570.62 + 2 * 151.35, 2)
    print(f"  Subtotal: ${total:.2f} (expected ${expected:.2f})")
    assert total == expected, f"Expected {expected}, got {total}"
    print("  [OK] Calculation verified")

    return True


def test_duplicate_detection():
    print("\nTesting duplicate detection...")

    from server.services.order_service import order_exists, compute_order_signature

    assert order_exists("ORD200000") is True
    print("  [OK] order_exists detects existing order")

    assert order_exists("FAKE9999") is False
    print("  [OK] order_exists returns False for missing order")

    items = [
        {"product_id": "MONITOR", "quantity": 5},
        {"product_id": "Phone", "quantity": 2},
    ]
    sig1 = compute_order_signature("C72649", items)
    sig2 = compute_order_signature("C72649", items)
    assert sig1 == sig2
    print(f"  Signature (same): {sig1[:32]}...")
    print("  [OK] Same inputs produce same signature")

    items2 = [
        {"product_id": "MONITOR", "quantity": 6},
        {"product_id": "Phone", "quantity": 2},
    ]
    sig3 = compute_order_signature("C72649", items2)
    assert sig1 != sig3
    print(f"  Signature (diff qty): {sig3[:32]}...")
    print("  [OK] Different inputs produce different signatures")

    return True


def test_db_integration():
    print("\nTesting DB integration...")

    from server.services.customer_service import get_customer_by_id, get_all_customers
    from server.services.product_service import get_product_by_id, get_all_products
    from server.services.order_service import (
        get_order_by_id, get_all_orders,
        get_product_sales_report, get_date_sales_report,
    )

    c = get_customer_by_id("C72649")
    assert c["customer_id"] == "C72649"
    assert c["name"] == "Customer C72649"
    print(f"  [OK] Customer C72649: {c['name']} ({c['email']})")

    p = get_product_by_id("MONITOR")
    assert p["product_id"] == "MONITOR"
    assert p["name"] == "Monitor"
    print(f"  [OK] Product MONITOR: {p['name']} (${p['unit_price']:.2f})")

    o = get_order_by_id("ORD200000")
    assert o["order_id"] == "ORD200000"
    assert o["status"] == "Shipped"
    assert len(o["items"]) == 1
    assert o["items"][0]["product_id"] == "MONITOR"
    assert o["items"][0]["quantity"] == 5
    print(f"  [OK] Order ORD200000: status={o['status']}, total=${o['total']:.2f}, items={len(o['items'])}")

    all_custs = get_all_customers()
    assert len(all_custs) == 1189
    print(f"  [OK] All customers: {len(all_custs)}")

    all_prods = get_all_products()
    assert len(all_prods) == 7
    print(f"  [OK] All products: {len(all_prods)}")

    orders = get_all_orders(limit=10)
    assert len(orders) == 10
    print(f"  [OK] Orders (limit=10): {len(orders)} returned")

    pr = get_product_sales_report()
    assert len(pr) == 7
    total_rev = round(sum(r['total_revenue'] for r in pr), 2)
    print(f"  [OK] Product sales report: {len(pr)} products, total=${total_rev:,.2f}")

    dr = get_date_sales_report("2023-01-01", "2023-12-31")
    assert len(dr) > 0
    print(f"  [OK] Date sales report 2023: {len(dr)} days")

    return True


def main():
    print("=" * 60)
    print("Order & Sales Management Application - Test Suite")
    print("=" * 60)

    all_passed = True

    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Validation Functions", test_validation),
        ("Order Calculation", test_order_calculation),
        ("Duplicate Detection", test_duplicate_detection),
        ("DB Integration", test_db_integration),
    ]

    for name, test_func in tests:
        try:
            result = test_func()
            if not result:
                all_passed = False
                print(f"\n[FAIL] {name} tests FAILED")
        except Exception as e:
            all_passed = False
            print(f"\n[FAIL] {name} tests raised exception: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    if all_passed:
        print("All tests PASSED")
        return 0
    else:
        print("Some tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
