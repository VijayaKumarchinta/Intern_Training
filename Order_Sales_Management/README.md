# Order and Sales Management Application

## 1. Project Overview

The Order and Sales Management Application is a web-based application designed to simulate the order processing and sales operations of a retail or e-commerce business.

The application manages customer orders, validates order details, calculates order totals, tracks order statuses, identifies duplicate orders, and generates product-wise and date-wise sales reports.

The application follows a three-tier architecture using Vue.js for the frontend, Flask for the backend, and PostgreSQL for data storage.

## 2. Project Objectives

The primary objectives are to:

- Manage customer orders and their associated order details.
- Validate order information before processing.
- Calculate order totals accurately.
- Track order statuses throughout the order lifecycle.
- Identify duplicate order submissions.
- Generate product-wise sales reports.
- Generate date-wise sales reports.
- Maintain data consistency through appropriate database operations.
- Separate frontend presentation, backend business logic, and database access.

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Vue.js | Frontend interface |
| JavaScript | Frontend application logic |
| Flask | Backend REST API |
| Python | Business logic and validation |
| PostgreSQL | Relational database |
| SQL | Data retrieval, order persistence, and sales aggregation |
| Postman | API testing |
| Git | Version control |

## 4. System Architecture

The application uses a traditional three-tier architecture.

```text
+----------------------------------+
|          Vue.js Frontend         |
|----------------------------------|
| Customer Orders                  |
| Order Validation Feedback        |
| Order Details and Status         |
| Product-wise Sales Report        |
| Date-wise Sales Report           |
+----------------------------------+
                 |
                 | HTTP / JSON
                 v
+----------------------------------+
|           Flask Backend          |
|----------------------------------|
| Order Management                 |
| Request Validation               |
| Duplicate Order Detection        |
| Order Total Calculation          |
| Order Status Management          |
| Sales Report Generation          |
+----------------------------------+
                 |
                 | SQL
                 v
+----------------------------------+
|          PostgreSQL              |
|----------------------------------|
| Existing Database Tables         |
| Customer and Order Data          |
| Product and Sales Data           |
+----------------------------------+
```

### Frontend responsibilities

- Display customer orders and order details.
- Collect order information.
- Submit requests to the Flask API.
- Display validation errors and processing results.
- Display order statuses.
- Present product-wise and date-wise sales reports.

### Backend responsibilities

- Validate incoming order requests.
- Retrieve authoritative product information.
- Calculate order totals.
- Apply duplicate-order detection rules.
- Enforce permitted order-status transitions.
- Persist order information.
- Generate sales reports using database queries.

### Database responsibilities

- Store and retrieve customer, product, and order information according to the existing schema.
- Maintain relational integrity through existing constraints.
- Support transactional order processing.
- Provide the data required for sales aggregation.

## 5. Core Functional Requirements

### 5.1 Customer Order Management

The application must manage customer orders and their associated details.

Expected functionality:

- Create an order for a customer.
- Associate one or more products with an order.
- Record product quantities and applicable prices.
- Retrieve order details.
- List customer orders according to the application's access rules.
- Update order information when permitted by the business rules.

Each order should have a unique identifier and contain sufficient information to identify the customer, ordered products, quantities, total amount, and current status, as supported by the existing database structure.

### 5.2 Order Validation

The application must validate order details before processing or saving an order.

Validation should include:

- Required order fields are provided.
- The customer identifier is valid.
- At least one order line is provided, if required.
- Product identifiers refer to valid, orderable products.
- Quantities are positive integers.
- Product prices are retrieved from the database rather than trusted from the frontend.
- Product availability is checked if inventory is part of the existing data model.
- The order request follows the expected data format.

Invalid orders must be rejected with a meaningful error message.

The backend must enforce all critical validation rules, even if the frontend performs preliminary validation.

### 5.3 Order Total Calculation

The application must calculate the total amount of an order based on its products, quantities, and applicable prices.

**Line total:**

`Line Total = Unit Price × Quantity`

**Order total:**

`Order Total = Sum of All Line Totals`

For example:

| Product | Unit Price | Quantity | Line Total |
|---|---:|---:|---:|
| Product A | 500.00 | 2 | 1,000.00 |
| Product B | 250.00 | 3 | 750.00 |
| **Order Total** | | | **1,750.00** |

The values above are illustrative.

Calculation requirements:

- Retrieve authoritative unit prices from PostgreSQL.
- Calculate line totals on the backend.
- Calculate the final order total on the backend.
- Use appropriate decimal arithmetic for monetary values.
- Apply consistent rounding rules.
- Store or return calculated totals according to the existing data model.

Taxes, discounts, shipping charges, and refunds should only be included if they are part of the agreed business requirements.

### 5.4 Order Status Tracking

The application must track the current status of each order.

A possible order lifecycle is:

```text
Pending
   |
   v
Confirmed
   |
   v
Processing
   |
   v
Shipped
   |
   v
Delivered
```

Cancellation may be permitted from selected statuses according to the business rules.

The application must:

- Display the current order status.
- Allow permitted status updates.
- Reject invalid status transitions.
- Prevent unauthorized status changes.
- Persist the updated status.
- Return the current status after a successful update.

The status values and transition rules must be aligned with the existing database structure and agreed business requirements.

Historical status tracking is optional unless explicitly required and supported by the existing schema.

### 5.5 Duplicate Order Detection

The application must identify duplicate order submissions and prevent accidental duplicate processing where the available database design supports it.

Duplicate submissions may occur because of:

- Repeated button clicks.
- Browser retries.
- Network interruptions.
- Client resubmission of the same request.

The recommended approach is **idempotency-based duplicate protection**.

Expected behavior:

- A new valid submission is processed normally.
- A retry using the same supported idempotency key returns the original result.
- Reusing the same key with a different request is rejected.
- Concurrent retries do not create multiple orders when durable idempotency is implemented.

Identical products and quantities do not necessarily indicate a duplicate business order; customers may legitimately place the same order more than once.

The actual duplicate-detection mechanism must be selected after inspecting the existing database schema. If durable idempotency cannot be supported without a schema change, document the limitation rather than claiming guaranteed duplicate prevention.

### 5.6 Product-wise Sales Reports

The application must generate sales summaries grouped by product.

The report may include:

- Product identifier.
- Product name.
- Quantity sold.
- Total sales amount.
- Number of orders containing the product, if required.

Example:

| Product | Quantity Sold | Total Sales |
|---|---:|---:|
| Product A | 25 | 12,500.00 |
| Product B | 18 | 9,000.00 |
| Product C | 12 | 6,000.00 |

These values are illustrative and are not actual database results.

The report must aggregate the relevant order data and apply the agreed rules for order statuses and sales calculations.

### 5.7 Date-wise Sales Reports

The application must generate sales summaries grouped by date.

The report may include:

- Order date.
- Number of orders.
- Quantity sold.
- Total sales amount.

Example:

| Date | Number of Orders | Total Sales |
|---|---:|---:|
| 2026-10-01 | 12 | 18,500.00 |
| 2026-10-02 | 9 | 12,250.00 |
| 2026-10-03 | 15 | 21,000.00 |

These values are illustrative.

The report should support a selected date range and define which timestamp determines the reporting date. Date boundaries and timezone handling must be consistent.

The application must also define whether cancelled orders, discounts, tax, shipping, and refunds affect the reported totals.

## 6. Order Processing Workflow

```text
Customer Selects Products
           |
           v
      Submit Order
           |
           v
   Validate Order Details
           |
           v
   Verify Products and Prices
           |
           v
   Detect Duplicate Submission
           |
           v
    Calculate Order Total
           |
           v
   Persist Order Transactionally
           |
           v
    Assign / Return Status
           |
           v
      Track Order Status
           |
           v
   Generate Sales Reports
```

### Workflow explanation

1. The frontend collects the customer and order details.
2. Vue.js sends the order request to Flask.
3. Flask validates the request.
4. The backend retrieves product information and authoritative prices.
5. The backend checks for a repeated submission using the supported duplicate-detection mechanism.
6. The backend calculates line totals and the order total.
7. The order and its associated lines are persisted in a database transaction where supported by the existing schema.
8. The application returns the order identifier, total, and status.
9. Authorized users can retrieve order details and perform permitted status updates.
10. Sales reports aggregate eligible order data by product or date.

## 7. Database Integration

The application must use the existing PostgreSQL database.

| Configuration | Value |
|---|---|
| Database system | PostgreSQL |
| Database name | `machine_monitor_db` |
| Target schema | `Order_sales_schema` |

### Database integration requirements

Before implementing queries, inspect the actual database structure and verify:

- Existing table and column names.
- Primary and foreign keys.
- Unique constraints.
- Column data types and nullability.
- Customer-to-order relationships.
- Order-to-product relationships.
- Price and quantity representations.
- Order-status representation.
- Existing support for duplicate detection.
- Columns required for product-wise and date-wise reporting.

Do not assume that tables named `customers`, `products`, `orders`, or `order_lines` exist until verified.

**Database modification restriction:** the application must not create, alter, drop, truncate, or seed database objects without explicit approval. If a required capability is missing, document the gap and request approval before proposing a schema change.

All database queries must use parameterized SQL. Related order writes must use transactions where applicable to prevent partially persisted orders.

## 8. Suggested Project Structure

```text
order-sales-management/
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── views/
│       ├── services/
│       ├── router/
│       └── App.vue
│
├── backend/
│   ├── app/
│   │   ├── routes/
│   │   │   ├── orders.py
│   │   │   └── reports.py
│   │   ├── services/
│   │   │   ├── order_service.py
│   │   │   └── report_service.py
│   │   ├── repositories/
│   │   │   ├── order_repository.py
│   │   │   └── report_repository.py
│   │   ├── validators/
│   │   │   └── order_validator.py
│   │   ├── config.py
│   │   └── __init__.py
│   │
│   ├── tests/
│   ├── requirements.txt
│   └── run.py
│
├── docs/
│   ├── database-discovery.md
│   ├── api-contracts.md
│   └── business-rules.md
│
├── .env.example
├── .gitignore
└── README.md
```

This is a proposed structure. It should be adapted to the existing repository rather than replacing files unnecessarily.

## 9. REST API Design

The following endpoints are proposed. Their implementation depends on the verified database structure and agreed API contracts.

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/orders` | Create an order |
| GET | `/api/orders` | Retrieve permitted orders |
| GET | `/api/orders/<id>` | Retrieve order details |
| PATCH | `/api/orders/<id>/status` | Update an order status |
| GET | `/api/reports/sales/by-product` | Generate product-wise sales |
| GET | `/api/reports/sales/by-date` | Generate date-wise sales |
| GET | `/api/health` | Check application health |

### Example order request

```json
{
  "items": [
    {
      "product_id": "PRODUCT_ID",
      "quantity": 2
    },
    {
      "product_id": "ANOTHER_PRODUCT_ID",
      "quantity": 1
    }
  ]
}
```

The identifiers are placeholders. The actual request must match the verified product identifier types.

The frontend should not be trusted to supply the final order total.

### Example successful response

```json
{
  "data": {
    "order_id": "GENERATED_ORDER_ID",
    "status": "Pending",
    "total": "1750.00"
  }
}
```

### Example validation error

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Quantity must be a positive integer."
  }
}
```

Use consistent response structures and suitable HTTP status codes for validation errors, missing resources, conflicts, and unexpected failures.

## 10. Environment Configuration

Database credentials must be stored outside source code.

Example `.env.example`:

```dotenv
FLASK_ENV=development
SECRET_KEY=
DATABASE_URL=
DB_SCHEMA=Order_sales_schema
FRONTEND_ORIGIN=http://localhost:5173
```

These are configuration placeholders. Use the connection format required by the selected PostgreSQL driver.

Never commit actual credentials or secret keys.

## 11. Testing Strategy

### Order management tests

- Create an order with valid details.
- Retrieve an existing order.
- Reject invalid customer or product identifiers.
- Reject missing required fields.
- Reject zero, negative, or non-integer quantities.

### Calculation tests

- Verify line totals.
- Verify order totals for multiple products.
- Verify monetary precision and rounding.
- Confirm that client-supplied totals cannot override backend calculations.

### Duplicate detection tests

- Submit a new order.
- Retry the same submission using the supported idempotency mechanism.
- Reuse a key with different request content.
- Test concurrent repeated submissions.
- Verify that separate legitimate orders are not incorrectly rejected.

### Status tracking tests

- Verify permitted status transitions.
- Reject invalid transitions.
- Reject unauthorized status updates.
- Confirm that successful changes are persisted.

### Reporting tests

- Verify product-wise quantity and sales aggregates.
- Verify date-wise order counts and totals.
- Test date-range boundaries.
- Verify treatment of cancelled orders and other applicable adjustments.

Use an isolated test database. Do not run destructive tests against production.

## 12. Error Handling

The application must handle:

- Invalid order details.
- Unknown customers or products.
- Invalid quantities.
- Duplicate submissions.
- Invalid order-status transitions.
- Database connection failures.
- Transaction failures.
- Invalid report filters.

Use consistent error responses and appropriate HTTP status codes.

Unexpected server errors must not expose SQL statements, credentials, or internal stack traces to users. Failed transactional operations must be rolled back.

## 13. Acceptance Criteria

The application is considered complete when:

- [ ] Customer orders can be created and retrieved.
- [ ] Order details are validated by the backend.
- [ ] Order totals are calculated accurately on the server.
- [ ] Invalid orders are rejected without partial persistence.
- [ ] Order statuses can be tracked and updated according to defined rules.
- [ ] Duplicate order submissions are identified using a documented mechanism.
- [ ] Product-wise sales reports return verified aggregates.
- [ ] Date-wise sales reports return verified aggregates.
- [ ] Database queries use parameterized SQL.
- [ ] Database transactions are used where required.
- [ ] Automated tests cover expected behavior and failure cases.
- [ ] The existing database schema remains unchanged without explicit approval.

## 14. Conclusion

The Order and Sales Management Application focuses on six core business capabilities: customer order management, order validation, order total calculation, order status tracking, duplicate order detection, and product-wise and date-wise sales reporting.

The Vue.js frontend provides the user interface, Flask implements the business rules and REST API, and PostgreSQL supplies the persistent data and reporting queries.

The implementation must prioritize accurate calculations, reliable order persistence, controlled status transitions, meaningful duplicate detection, and correct sales aggregates while remaining compatible with the verified existing database structure.