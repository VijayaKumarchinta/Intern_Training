"""db/load_data.py - Import CSV into machine_sensor_db (per-row commit)."""
import csv
import sys
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

SCRIPT_DIR  = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
CSV_PATH    = PROJECT_DIR / "data" / "Online_Store_Orders.csv"

SERVER_DIR = PROJECT_DIR / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from dotenv import load_dotenv
load_dotenv(SERVER_DIR / ".env")

from app import create_app
from app.extensions import db
from app.models import Customer, Order, OrderItem, Product
from app.services.order_service import VALID_STATUSES



DATE_OPTIONAL_FOR = {"Cancelled", "Returned"}


def _to_decimal(s):
    try:
        return Decimal(str(s).strip())
    except (InvalidOperation, TypeError, ValueError):
        return None


def _to_date(s):
    try:
        return date.fromisoformat(str(s).strip())
    except (TypeError, ValueError):
        return None


def _first(row, *keys):
    for k in keys:
        v = row.get(k)
        if v is not None and str(v).strip() != "":
            return str(v).strip()
    return ""


def import_csv():
    if not CSV_PATH.exists():
        print(f"[FATAL] CSV not found: {CSV_PATH}", file=sys.stderr)
        return 1

    app = create_app()
    with app.app_context():
        stats = {"rows": 0, "imported": 0, "rejected": 0, "dup": 0}
        seen_products = {}

        with CSV_PATH.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for lineno, row in enumerate(reader, start=2):
                stats["rows"] += 1
                try:
                    qty_raw     = _first(row, "Quantity", "Qty")
                    price_raw   = _first(row, "UnitPrice", "Unit Price", "Price")
                    prod_name   = _first(row, "Product", "ProductName", "Product Name")
                    cust_id     = _first(row, "CustomerID", "Customer ID", "CustomerId")
                    order_id    = _first(row, "OrderID", "Order ID", "OrderId")
                    order_date  = _first(row, "OrderDate", "Order Date", "Date")
                    status_raw  = _first(row, "OrderStatus", "Order Status", "Status")
                    cust_name   = _first(row, "CustomerName", "Customer Name", "Name") or cust_id
                    cust_email  = _first(row, "Email", "CustomerEmail", "Customer Email") or None

                    if not prod_name or not cust_id or not order_id:
                        raise ValueError("missing Product / CustomerID / OrderID")
                    try:
                        qty = int(qty_raw)
                    except ValueError:
                        raise ValueError(f"invalid quantity {qty_raw!r}")
                    if qty <= 0:
                        raise ValueError(f"quantity must be > 0, got {qty}")

                    price = _to_decimal(price_raw)
                    if price is None or price < 0:
                        raise ValueError(f"invalid price {price_raw!r}")

                    od = _to_date(order_date) if order_date else None
                    if order_date and od is None:
                        raise ValueError(f"invalid date {order_date!r}")

                    if not status_raw:
                        raise ValueError("missing OrderStatus")
                    if status_raw not in VALID_STATUSES:
                        raise ValueError(f"invalid status {status_raw!r} (allowed: {sorted(VALID_STATUSES)})")
                    if od is None and status_raw not in DATE_OPTIONAL_FOR:
                        raise ValueError(
                            f"date required for status {status_raw!r} "
                            f"(only {sorted(DATE_OPTIONAL_FOR)} may omit it)"
                        )

                    prod = seen_products.get(prod_name)
                    if prod is None:
                        prod = Product.query.filter_by(pro_name=prod_name).first()
                        if prod is None:
                            prod = Product(pro_name=prod_name, current_price=price)
                            db.session.add(prod)
                            db.session.flush()
                        seen_products[prod_name] = prod
                    elif prod.current_price is None:
                        prod.current_price = price

                    cust = db.session.get(Customer, cust_id)
                    if cust is None:
                        cust = Customer(customer_id=cust_id, cust_name=cust_name, email=cust_email)
                        db.session.add(cust)
                        db.session.flush()

                    order = db.session.get(Order, order_id)
                    if order is None:
                        order = Order(
                            order_id=order_id,
                            customer_id=cust_id,
                            order_date=od,
                            order_status=status_raw,   
                        )
                        db.session.add(order)
                        db.session.flush()

                    existing = OrderItem.query.filter_by(
                        order_id=order_id, product_id=prod.product_id
                    ).first()
                    if existing is not None:
                        existing.quantity += qty
                        stats["dup"] += 1
                    else:
                        db.session.add(OrderItem(
                            order_id=order_id,
                            product_id=prod.product_id,
                            quantity=qty,
                            unit_price=price,
                        ))

                    db.session.commit()
                    stats["imported"] += 1

                except Exception as exc:
                    db.session.rollback()
                    stats["rejected"] += 1
                    print(f"[row {lineno}] REJECTED: {exc}", file=sys.stderr)

        print("=" * 60)
        print(f"Rows read:   {stats['rows']}")
        print(f"Imported:    {stats['imported']}")
        print(f"Duplicates:  {stats['dup']}  (merged)")
        print(f"Rejected:    {stats['rejected']}")
        print("=" * 60)
        return 0 if stats["rejected"] == 0 else 2

if __name__ == "__main__":
    sys.exit(import_csv())