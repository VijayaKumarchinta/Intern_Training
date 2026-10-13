# Order & Sales Management - Routes Package
from .customer_routes import customer_bp
from .product_routes import product_bp
from .order_routes import order_bp
from .report_routes import report_bp

__all__ = ['customer_bp', 'product_bp', 'order_bp', 'report_bp']
