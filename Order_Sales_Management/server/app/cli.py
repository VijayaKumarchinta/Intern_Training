import click

from app.extensions import db
from app import models
from app.services.order_service import validate_order


def register_cli(app):
    @app.cli.command("validate-orders")
    def validate_orders():
        pending = (
            db.session.execute(db.select(models.Order).where(models.Order.is_valid.is_(False)))
            .scalars()
            .all()
        )

        checked = 0
        valid = 0
        invalid = 0

        for order in pending:
            row = {
                "order_id": order.order_id,
                "order_date": order.order_date,
                "customer_id": order.customer_id,
                "product": order.product,
                "quantity": order.quantity,
                "unit_price": order.unit_price,
                "order_status": order.order_status,
            }
            errors = validate_order(row)
            checked += 1
            if errors:
                order.is_valid = False
                order.validation_errors = "; ".join(errors)
                invalid += 1
            else:
                order.is_valid = True
                order.validation_errors = None
                valid += 1

        db.session.commit()
        click.echo({"checked": checked, "valid": valid, "invalid": invalid})
