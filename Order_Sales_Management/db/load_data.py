import csv
from datetime import date
from decimal import Decimal
from app import create_app
from app.models import Customer, Product, Order, OrderItem
from app.extensions import db

app = create_app()

with app.app_context():
    # Map product names to IDs
    products = {p.pro_name: p.product_id for p in Product.query.all()}
    
    # Track customers to avoid duplicate creation
    seen_customers = set()
    
    with open('../data/Online_Store_Orders.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Skip invalid rows (Quantity = 'two', negative prices)
                if not row['Quantity'].isdigit():
                    continue
                
                qty = int(row['Quantity'])
                if qty <= 0:
                    continue
                
                price = Decimal(row['UnitPrice'])
                if price < 0:
                    continue
                
                order_date = date.fromisoformat(row['Date']) if row['Date'] else None
                
                # Create customer if not exists
                cust_id = row['CustomerID']
                if cust_id not in seen_customers:
                    if not db.session.get(Customer, cust_id):
                        cust = Customer(customer_id=cust_id, cust_name=f"Customer {cust_id}")
                        db.session.add(cust)
                    seen_customers.add(cust_id)
                
                # Create Order
                order = Order(
                    order_id=row['OrderID'],
                    customer_id=cust_id,
                    order_date=order_date,
                    order_status=row['OrderStatus']
                )
                db.session.add(order)
                
                # Create OrderItem
                item = OrderItem(
                    order_id=row['OrderID'],
                    product_id=products[row['Product']],
                    quantity=qty,
                    unit_price=price
                )
                db.session.add(item)
                
            except Exception as e:
                print(f"Skipping row {row['OrderID']}: {e}")
        
        db.session.commit()
        print(f"Loaded orders successfully")