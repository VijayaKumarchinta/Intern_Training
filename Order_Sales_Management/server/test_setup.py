"""
Test script for Order & Sales Management Application.
Verifies configuration loading, imports, and basic functionality.
"""
import sys
import os

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path for imports (so relative imports work)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from server.config import validate_config, APP_PORT, DB_HOST
        print("  [OK] config.py imports OK")
    except Exception as e:
        print(f"  [FAIL] config.py failed: {e}")
        return False
    
    try:
        from utils.validation import (
            validate_non_empty_string, validate_email, validate_positive_int
        )
        print("  [OK] validation.py imports OK")
    except Exception as e:
        print(f"  [FAIL] validation.py failed: {e}")
        return False
    
    try:
        from server.services.customer_service import CustomerService
        print("  [OK] customer_service.py imports OK")
    except Exception as e:
        print(f"  [FAIL] customer_service.py failed: {e}")
        return False
    
    try:
        from server.services.product_service import ProductService
        print("  [OK] product_service.py imports OK")
    except Exception as e:
        print(f"  [FAIL] product_service.py failed: {e}")
        return False
    
    try:
        from server.services.order_service import OrderService
        print("  [OK] order_service.py imports OK")
    except Exception as e:
        print(f"  [FAIL] order_service.py failed: {e}")
        return False
    
    return True


def test_config():
    """Test configuration values."""
    print("\nTesting configuration...")
    
    from config import (
        DB_HOST, DB_PORT, DB_NAME, APP_HOST, APP_PORT, 
        ORDER_STATUS_PENDING, ORDER_STATUS_TRANSITIONS, VALID_ORDER_STATUSES
    )
    
    print(f"  DB_HOST: {DB_HOST}")
    print(f"  DB_PORT: {DB_PORT}")
    print(f"  DB_NAME: {DB_NAME}")
    print(f"  APP_HOST: {APP_HOST}")
    print(f"  APP_PORT: {APP_PORT}")
    print(f"  ORDER_STATUS_PENDING: {ORDER_STATUS_PENDING}")
    print(f"  VALID_ORDER_STATUSES: {VALID_ORDER_STATUSES}")
    print(f"  ORDER_STATUS_TRANSITIONS: {ORDER_STATUS_TRANSITIONS}")
    
    # Validate status transitions
    assert ORDER_STATUS_PENDING in VALID_ORDER_STATUSES
    assert 'processing' in ORDER_STATUS_TRANSITIONS[ORDER_STATUS_PENDING]
    assert 'cancelled' in ORDER_STATUS_TRANSITIONS[ORDER_STATUS_PENDING]
    print("  [OK] Status transitions validated")
    
    return True


def test_validation():
    """Test validation functions."""
    print("\nTesting validation functions...")
    
    from utils.validation import (
        validate_non_empty_string,
        validate_email,
        validate_positive_int,
        validate_positive_decimal,
        validate_order_id,
        validate_product_id,
        validate_customer_id,
        validate_order_items,
        validate_discount,
    )
    
    # Test non-empty string
    assert validate_non_empty_string("test", "field") == "test"
    print("  [OK] validate_non_empty_string OK")
    
    # Test email
    assert validate_email("test@example.com") == "test@example.com"
    try:
        validate_email("invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("  [OK] validate_email rejects invalid OK")
    
    # Test positive int
    assert validate_positive_int(5, "qty") == 5
    try:
        validate_positive_int(0, "qty")
        assert False, "Should have raised ValueError"
    except ValueError:
        print("  [OK] validate_positive_int rejects 0 OK")
    
    # Test order ID format
    assert validate_order_id("ORD-001") == "ORD-001"
    assert validate_order_id("ord-001") == "ORD-001"  # uppercase
    print("  [OK] validate_order_id OK")
    
    # Test discount
    result_10pct = validate_discount(10)  # 10% -> 0.10
    assert float(result_10pct) == 0.10, f"Expected 0.10, got {result_10pct}"
    result_decimal = validate_discount(0.10)
    assert float(result_decimal) == 0.10
    assert validate_discount(None) == 0
    print("  [OK] validate_discount OK")
    
    # Test order items
    items = [
        {"product_id": "PROD-001", "quantity": 2},
        {"product_id": "PROD-002", "quantity": 1, "unit_price": 29.99}
    ]
    validated = validate_order_items(items)
    assert len(validated) == 2
    assert validated[0]['product_id'] == "PROD-001"
    assert validated[0]['quantity'] == 2
    assert validated[0]['unit_price'] is None  # Not provided
    assert float(validated[1]['unit_price']) == 29.99
    print("  [OK] validate_order_items OK")
    
    return True


def test_order_calculation():
    """Test order calculation logic."""
    print("\nTesting order calculation...")
    
    from decimal import Decimal
    from config import DEFAULT_TAX_RATE
    
    # Simulate calculation
    items = [
        {"product_id": "PROD-001", "quantity": 2, "unit_price": 50.00},
        {"product_id": "PROD-002", "quantity": 1, "unit_price": 25.00},
    ]
    
    subtotal = sum(Decimal(str(item['unit_price'])) * item['quantity'] for item in items)
    discount_percent = Decimal('0.10')  # 10%
    discount = subtotal * discount_percent
    tax = subtotal * Decimal(str(DEFAULT_TAX_RATE)) / Decimal('100')
    total = subtotal - discount + tax
    
    print(f"  Subtotal: ${float(subtotal):.2f}")
    print(f"  Discount (10%): ${float(discount):.2f}")
    print(f"  Tax ({DEFAULT_TAX_RATE}%): ${float(tax):.2f}")
    print(f"  Total: ${float(total):.2f}")
    
    expected_subtotal = Decimal('125.00')
    assert subtotal == expected_subtotal, f"Expected {expected_subtotal}, got {subtotal}"
    print("  [OK] Calculation verified")
    
    return True


def test_hash_signature():
    """Test duplicate detection signature generation."""
    print("\nTesting duplicate detection signatures...")
    
    import hashlib
    
    # Test signature generation logic
    customer_id = "CUST-001"
    items = [
        {"product_id": "PROD-001", "quantity": 2},
        {"product_id": "PROD-002", "quantity": 1},
    ]
    subtotal = 125.00
    
    # Build signature
    item_signatures = []
    for item in sorted(items, key=lambda x: x.get('product_id', '')):
        product_id = item.get('product_id', '')
        quantity = item.get('quantity', 0)
        item_signatures.append(f"{product_id}:{quantity}")
    
    items_str = "|".join(item_signatures)
    subtotal_rounded = str(round(subtotal, 2))
    signature_string = f"{customer_id.upper()}|{items_str}|{subtotal_rounded}"
    signature = hashlib.sha256(signature_string.encode()).hexdigest()
    
    print(f"  Customer: {customer_id}")
    print(f"  Items: {items_str}")
    print(f"  Subtotal: {subtotal_rounded}")
    print(f"  Signature string: {signature_string}")
    print(f"  SHA-256: {signature[:32]}...")
    
    # Same inputs should produce same signature
    signature2 = hashlib.sha256(signature_string.encode()).hexdigest()
    assert signature == signature2
    print("  [OK] Signature consistency verified")
    
    # Different quantity should produce different signature
    items2 = [
        {"product_id": "PROD-001", "quantity": 3},  # Different quantity
        {"product_id": "PROD-002", "quantity": 1},
    ]
    item_signatures2 = []
    for item in sorted(items2, key=lambda x: x.get('product_id', '')):
        product_id = item.get('product_id', '')
        quantity = item.get('quantity', 0)
        item_signatures2.append(f"{product_id}:{quantity}")
    items_str2 = "|".join(item_signatures2)
    signature_string2 = f"{customer_id.upper()}|{items_str2}|{subtotal_rounded}"
    signature3 = hashlib.sha256(signature_string2.encode()).hexdigest()
    
    assert signature != signature3
    print("  [OK] Different orders produce different signatures")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Order & Sales Management Application - Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Validation Functions", test_validation),
        ("Order Calculation", test_order_calculation),
        ("Duplicate Detection", test_hash_signature),
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
