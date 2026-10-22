from ..constants import Role

def is_admin(user):
    return user is not None and user.role == Role.ADMIN.value

def is_customer(user):
    return user is not None and user.role == Role.CUSTOMER.value

def owns_customer(user, customer_id):
    if user is None or not customer_id:
        return False
    customer = getattr(user, "customer", None)
    return customer is not None and customer.customer_id == customer_id

def can_view_order(user, order):
    if user is None or order is None:
        return False
    if is_admin(user):
        return True
    customer = getattr(order, "customer", None)
    return customer is not None and customer.user_id == user.id