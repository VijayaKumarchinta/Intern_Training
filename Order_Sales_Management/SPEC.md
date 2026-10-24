# Order & Sales Management — API Specification (Source of Truth)

This document supersedes README.md and Backend.md wherever they conflict.
Approved by: <Swaroop> on <date>

## Roles
- admin: full access
- customer: own orders only

## Auth
POST /api/auth/register          Public   body: email, password, full_name, customer_id
POST /api/auth/verify            Public   body: email, code, customer_id (optional)
POST /api/auth/resend-verification Public body: email
POST /api/auth/login             Public   body: email, password  -> {access_token, user}
POST /api/auth/forgot-password   Public   body: email
POST /api/auth/reset-password    Public   body: token, new_password
GET  /api/auth/me                Auth     -> user (+customer if linked)

Verify flow: 6-digit OTP, POST /api/auth/verify, TTL 2 min, max 3 attempts.
Unverified login -> 401.
Malformed/expired JWT -> 401 (NOT 422).

## Orders
GET   /api/orders                Auth     customer=own, admin=all; ?status=&customer_id=&page=&per_page=
GET   /api/orders/<order_id>     Auth     customer=own (404 if not), admin=any
POST  /api/orders                Admin    server sets unit_price from products.current_price
POST  /api/orders/validate       Admin    dry-run
PATCH /api/orders/<order_id>/status Admin
GET   /api/orders/duplicates     Admin
POST  /api/import/orders         Admin    multipart CSV -> staging -> validate -> commit

## Customers & Products
GET   /api/customers             Admin    paginated
GET   /api/products              Auth     list with current_price
PATCH /api/customers/<id>/link   Admin    body: user_id

## Reports
GET /api/reports/product-wise    Admin
GET /api/reports/date-wise       Admin    ?group=day|month
Only Shipped and Delivered count. Revenue = quantity * order_item.unit_price.

## Database
Name: order_sales_db
Schema: order_sales

## Pricing rule
create_order MUST ignore any client-supplied unit_price and read
products.current_price at the time of the order.
