# Server App Modules

This document explains the current server-side code in `server/`.

## Project structure

```text
server/
├── .env
├── .env.example
├── requirements.txt
├── run.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── models.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── decorators.py
│   └── services/
│       ├── __init__.py
│       └── order_service.py
```

## Entry point

`run.py` starts the Flask app:

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
```

It uses the app factory from `app/__init__.py`.

## App factory

File: `app/__init__.py`

This creates the Flask application:

- loads configuration from `Config`
- initializes `db`, `jwt`, `mail`
- registers a few basic routes

Current routes:

- `GET /` — simple readiness message
- `GET /health` — returns `{"status": "ok"}`
- `GET /db` — returns counts for orders, customers, and users from the database

This file is intentionally small. It wires the app together and leaves business logic to the services.

## Configuration

File: `app/config.py`

This reads environment variables and exposes them as Flask config.

Key points:

- `DATABASE_URL` is required. If it is missing, the app raises an error at startup.
- `JWT_SECRET_KEY` is required.
- The database connection uses `SQLALCHEMY_ENGINE_OPTIONS` so the `order_sales` schema is selected through `search_path`.
- JWT access token expiry defaults to 24 hours.
- Mail settings have defaults, but real email sending still needs real credentials.

Example `.env` entries:

```text
DATABASE_URL=postgresql+psycopg2://postgres:your_password@localhost:5432/machine_sensor_db
DB_SCHEMA=order_sales
JWT_SECRET_KEY=change-this-to-a-real-secret
JWT_ACCESS_TOKEN_EXPIRES_HOURS=24
```

## Extensions

File: `app/extensions.py`

This creates the shared Flask extensions:

- `db` — SQLAlchemy instance
- `jwt` — JWT manager
- `mail` — mail client
- `bcrypt` — password hashing helper

These are created once and then initialized by the app factory.

## Models

File: `app/models.py`

These map to the normalized `order_sales` schema.

### User

Represents a login account.

Important fields:

- `id`
- `email`
- `password_hash`
- `full_name`
- `role`, either `customer` or `admin`
- `is_verified`
- `verification_token_hash`, `verification_expires_at`
- `reset_token_hash`, `reset_token_expires_at`
- `created_at`, `updated_at`

Relations:

- one `User` may be linked to one `Customer`

### Customer

Represents a customer profile.

Important fields:

- `customer_id`, primary key
- `user_id`, unique foreign key to `users.id`
- `cust_name`
- `email`
- `created_at`

Relations:

- one `Customer` can have many `Order` records

### Product

Represents the product catalogue.

Important fields:

- `product_id`
- `pro_name`, unique
- `current_price`, optional

Relations:

- one `Product` can appear in many `OrderItem` records

### Order

Represents an order header.

Important fields:

- `order_id`, primary key
- `customer_id`, required foreign key to `customers.customer_id`
- `order_date`
- `order_status`
- `created_at`, `updated_at`

Relations:

- one `Order` can have many `OrderItem` records

### OrderItem

Represents one product line in an order.

Important fields:

- `order_item_id`
- `order_id`, foreign key to `orders.order_id`
- `product_id`, foreign key to `products.product_id`
- `quantity`
- `unit_price`

Constraints:

- `quantity` must be greater than 0
- `unit_price` must be >= 0
- unique on `(order_id, product_id)`

## Utility decorators

File: `app/utils/decorators.py`

### `role_required(required_role)`

A decorator that protects a route by JWT role.

What it does:

- expects a valid JWT to be present
- reads the `role` claim from the JWT
- if the role matches `required_role`, the route runs
- if the role does not match, it returns `{"error": "Forbidden"}` with status 403

Example:

```python
@role_required("admin")
def admin_route():
    ...
```

This is used for admin-only endpoints.

### `current_user()`

A helper that returns the currently authenticated user.

What it does:

- reads the user id from the JWT
- looks up that user in the `User` table
- returns the `User` object, or `None` if there is no valid identity

This is useful inside routes or services when you need the logged-in user.

## Order service

File: `app/services/order_service.py`

This contains the business logic for orders, reports, and duplicate detection.

### Validation

#### `validate_order_payload(payload)`

Validates an incoming order request.

Checks:

- `order_id` must be present and match the pattern `ORD####`
- `order_date` is required
- `customer_id` is required and must exist in the `customers` table
- `items` must be present and non-empty
- each item must have a valid `product_id` that exists in the `products` table
- duplicate `product_id` values in the same request are rejected
- `quantity` must be a valid number between 1 and 1000
- `unit_price` must be a valid number and not negative
- `order_status`, if provided, must be one of the valid statuses

Returns a list of error strings. If the list is empty, the payload is valid.

### Ownership and access

#### `visible_orders_for(user)`

Returns the orders a user is allowed to see.

Behavior:

- if the user is `None`, returns an empty query
- if the user is an admin, returns all orders
- otherwise, returns only the orders belonging to that customer

This enforces the rule that a customer sees only their own orders.

### Status workflow

#### `can_transition(old_status, new_status)`

Checks whether a status change is allowed.

Returns `True` or `False` based on the allowed transition rules.

#### `change_status(order, new_status)`

Applies a status change if it is allowed.

What it does:

- checks whether the transition is allowed
- if allowed, updates the order status and commits
- returns `True, None` on success
- returns `False, error_message` if the transition is not allowed

### Reports

#### `product_wise_report()`

Returns sales grouped by product.

Each result includes:

- `product`
- `items`
- `units`
- `revenue`

Only orders in sale statuses are included.

#### `date_wise_report(group="day")`

Returns sales grouped by time period.

If `group` is `"month"`, the report groups by month. Otherwise it groups by day.

Each result includes:

- `period`
- `orders`
- `units`
- `revenue`
- 

### Duplicate detection

#### `find_duplicates()`

Looks for repeated line-item patterns across orders.

Each result includes:

- `customer_id`
- `product_id`
- `quantity`
- `unit_price`
- `order_date`
- `occurrences`
- `order_ids`

This helps identify possible duplicate orders for review. It does not decide definitively whether they are duplicates.

## Current API surface

At the moment the server exposes only a few endpoints:

- `GET /`
- `GET /health`
- `GET /db`

The service layer and decorators are ready to support more endpoints, but those endpoints are not built yet.

## What is intentional

- The app is built around the normalized schema.
- Validation happens on write, not by storing invalid rows in the main tables.
- Orders are headers only. Product, quantity, and price live in `OrderItem`.
- Admin and customer access are separated by role.
- Reports are computed from `orders` joined to `order_items` and `products`.

## What is not built yet

- authentication endpoints such as register, login, verify, reset
- protected order endpoints
- protected report endpoints
- frontend integration
- email delivery beyond configuration

This document describes the server code as it exists now.
