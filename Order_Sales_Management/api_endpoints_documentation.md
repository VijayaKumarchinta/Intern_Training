## 1. "Manage customer orders"

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/orders` | List visible orders; supports status filtering and pagination. |
| GET | `/api/orders/<id>` | Retrieve a specific order and its line items. |
| POST | `/api/orders` | Create an order (Admin only). |
| GET | `/api/customers` | List customers (Admin only). |
| POST | `/api/customers` | Create a new customer (Admin only). |
| POST | `/api/products` | Create a product (Admin only). |
| PATCH | `/api/products/<id>` | Update a product's price (Admin only). |
| DELETE | `/api/products/<id>` | Delete a product if unused (Admin only). |
| GET | `/api/products` | List products (for dropdowns). |

## 2. "Validate order details"

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/orders` | Rejects invalid payloads (bad ID format, bad date, bad quantity, unknown customer/product) and returns a 400 with an error array. |

## 3. "Calculate order totals"

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/orders` | Returns calculated total (qty × historical price) and `item_count` in every order response. |
| GET | `/api/orders/<id>` | Returns the calculated total and individual line item totals. |

## 4. "Track order statuses"

| Method | Endpoint | Description |
|---|---|---|
| PATCH | `/api/orders/<id>/status` | Update order status, strictly enforcing the state machine (`ALLOWED_TRANSITIONS`). |

## 5. "Identify duplicate orders"

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/orders/duplicates` | Find duplicate order groups (matching customer, product, qty, price, date). |

## 6. "Generate product-wise and date-wise sales reports"

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/reports/product-wise` | Product-wise sales report. Supports `?format=csv` for download. |
| GET | `/api/reports/date-wise` | Daily or monthly sales report. Supports `?format=csv` for download. |
| GET | `/api/reports/summary` | Dashboard KPIs, charts, latest orders, and duplicate counts (Admin only). |

## "Should we implement user registration and login?"

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register an account (sends OTP). |
| POST | `/api/auth/login` | Authenticate and obtain a JWT. |
| GET | `/api/auth/me` | Retrieve the authenticated user profile. |

## "Do we need email verification during registration?"

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/verify` | Verify email using OTP and link the customer ID. |
| POST | `/api/auth/resend-verification` | Resend the verification code. |

## "Should we implement password reset functionality?"

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/forgot-password` | Initiate password reset. |
| POST | `/api/auth/reset-password` | Reset password using the token (invalidates old JWTs). |

## "Do we need different user roles, such as Admin and Customer?"

Enforced via `@role_required(Role.ADMIN.value)` on the following endpoints:

| Method | Endpoint |
|---|---|
| POST | `/api/orders` |
| PATCH | `/api/orders/<id>/status` |
| GET | `/api/orders/duplicates` |
| GET | `/api/customers` |
| POST | `/api/customers` |
| POST | `/api/products` |
| PATCH | `/api/products/<id>` |
| DELETE | `/api/products/<id>` |
| GET | `/api/reports/*` |

## "Should customers be able to view only their own orders, while admins can manage all orders?"

Enforced via `visible_orders_for()` and `can_view_order()`:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/orders` | Admins see all orders; Customers see only their own. |
| GET | `/api/orders/<id>` | Customers get 404 for other customers' orders; Admins can view any order. |
