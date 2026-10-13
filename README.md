# Order and Sales Management Application

A Vue.js + Flask + PostgreSQL application that simulates the order processing and sales
operations of a retail / e-commerce business.

This README is the implementation document for the `Application_Vue/` project. It is written
from the learning recorded in the Intern Training repository, especially:
- `INTERN_TRAINING_CONSOLIDATED.md`
- `TRAINING_DOCUMENTATION.md`
- `LIVE_MONITORING_ARCHITECTURE.md`
- `cheatsheet.md`
- `MQTT/Machine_Sensor_API/readme.md`
- the root architecture `.md`

It documents:
- what the application does
- the architecture and why it was chosen
- the 8 design principles and how they apply here
- how the database, SQL, and API concepts are intended to be used
- how my usage so far maps onto those concepts
- the files and folders expected now
- the files and folders planned for future implementation

## Stack
- Frontend: Vue.js
- Backend: Flask
- Database: PostgreSQL

## What this application does
- Manage customer orders
- Validate order details
- Calculate order totals
- Track order statuses
- Identify duplicate orders
- Generate product-wise and date-wise sales reports

## Why this stack and architecture
Traditional three-tier architecture is used deliberately because the application needs
explicit business rules, duplicate order handling, transactional order processing, and
sales reporting.

```
Vue.js  ->  Flask  ->  PostgreSQL
(frontend) (backend)  (database)
```

The frontend is the presentation layer only. The backend is the access-control and
data-contract boundary. The database is the persistent state. The browser must not connect
directly to PostgreSQL, and the API must not leak database internals to the client.

Alternatives considered:
- Backend-as-a-service, for example Supabase: simpler to start, but hides the backend
  engineering concepts this project is meant to exercise.
- Browser storage, for example localStorage: useful for offline features, but not suitable
  for shared transactional order data.

## 8 design principles and how they apply here
These principles are constraints on decisions, not excuses to add layers.

### 1. Cohesion and single responsibility
Each module should have one reason to change.
- Vue components own presentation and user interaction.
- API routes own HTTP parsing, validation delegation, status codes, and response shaping.
- Services own business rules and SQL.
- Database layer owns connections, pooling, and transaction policy.
- Reports should be computed by the backend, not recreated in the UI.

### 2. Encapsulation and abstraction
Internal details should be hidden behind a small, stable interface.
- Services expose behavior like `create_order`, `list_orders`, `update_status`, not raw SQL.
- The database layer exposes `connection()` and `cursor()` context managers, not pool
  internals.
- Vue components call a small API service layer instead of scattering `fetch` calls everywhere.

### 3. Loose coupling and modularity
Modules should depend on interfaces and shared contracts, not on each other's internals.
- The Flask app should be buildable through a factory so imports stay side-effect-free.
- The Vue app should depend on endpoint contracts, not on how the backend stores data.
- Shared validators and shared filter/report builders should live in one place so a rule
  change is made once.

### 4. Reusability and extensibility
Common behavior should be reusable without copy-paste.
- Validation helpers should be importable by every route that needs them.
- Pagination, filtering, and ordering should be built once and reused across list and report
  endpoints.
- If a new report is added later, it should reuse the same query-building and error-handling
  patterns.

### 5. Portability
The code should not depend on one machine, one IDE, or one secret source.
- Configuration comes from `.env` and is validated at boot.
- Secrets stay out of source control.
- Paths, credentials, and timeouts should be configurable, not hard-coded.

### 6. Defensibility
The system should fail in predictable, bounded ways.
- Validate at the boundary once, centrally.
- Use parameterized SQL everywhere; identifiers only through safe formatting.
- Use transactions for writes that must succeed or fail together.
- Use timeouts so a stuck database or slow query fails fast and visibly.
- Translate driver errors into honest HTTP status codes instead of blanket 500s.
- Log exceptions with context, but never leak internal details to clients.

### 7. Maintainability and testability
Code should be easy to change safely and easy to verify.
- Layers should be separable so services can be tested without a live database where possible.
- Shared logic should be extracted so tests cover the common path once.
- Changes should be verifiable: build parallel versions when needed, verify both chains, then
  promote.
- Documentation should record why, not just what.

### 8. Simplicity
Choose the simplest structure that actually solves the problem.
- No ORM, no repository pattern, no dependency-injection framework unless a concrete problem
  demands them.
- Plain SQL and three layers is the starting point if it solves the problem.
- YAGNI: do not add reports, queues, caching, or advanced deployment machinery before the
  application needs them.

## How the database is intended to be used
The database is the system of record for orders, customers, products, order lines, and status
history.

### Design direction
- One schema namespace for the application tables.
- Explicit tables with clear primary keys and foreign keys.
- `TIMESTAMPTZ` for timestamps so an instant means the same thing everywhere.
- Constraints only for claims that can be proven; business claims like duplicate detection
  should be enforced in the application layer when the source cannot guarantee them.
- Indexes for the query patterns the application actually uses, not for every column.

### Expected tables
- customers
- products
- orders
- order_lines
- order_statuses or an order status transition history table
- possibly a duplicate-tracking or idempotency table if the API supports retries

### Expected usage patterns
- Reads should be bounded and paginated where lists can grow.
- Writes that affect order totals, status, or line items should be transactional.
- Reports should be built from real data paths, not from in-memory reconstructions that can
  drift from the database.

## How SQL is intended to be used
SQL is the implementation language for persistence and reporting.

### Command categories in play
- DDL for schema: `CREATE`, `ALTER`, `DROP`, `TRUNCATE` as needed during setup.
- DQL for queries: `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`, `OFFSET`, `GROUP BY`, aggregates.
- DML for changes: `INSERT`, `UPDATE`, `DELETE`.
- TCL for transactional boundaries: `COMMIT`, `ROLLBACK`, and savepoints where appropriate.

### SQL habits to carry into this project
- `%s` placeholders for every data value.
- f-strings only for identifiers like schema or table names, never for data.
- `RETURNING` where the application needs the inserted or updated row.
- `ON CONFLICT` handling only where the conflict rule is real and provable.
- `execute_values` or equivalent batching for bulk work, with a bounded batch size.
- `rowcount` checks where an update or delete must be confirmed.
- Shared filter builders so list, export, and report queries do not drift apart.

### SQL habits to avoid
- String concatenation for values.
- Uniqueness rules that reflect a hope rather than a provable guarantee.
- Unbounded queries that can scan an entire table for a UI list or report.
- Business logic hidden in ad-hoc queries spread across many places.

## How the API is intended to be used
The API is the contract between Vue and PostgreSQL.

### Responsibilities
- Validate HTTP input before touching the database.
- Translate business rules into consistent responses.
- Return honest status codes.
- Keep error responses predictable and safe.
- Version or namespace endpoints so the frontend can depend on stable contracts.

### Expected endpoint themes
- Create order
- List orders with filters and status
- Get order details
- Update order status
- Detect duplicate orders
- Product-wise sales report
- Date-wise sales report

### Expected response discipline
- Success responses should be consistent in shape.
- Validation failures should be actionable.
- Duplicate or conflict cases should be distinguishable from generic server errors.
- The API should not return raw database errors or internal details to the client.
- Snapshot-style responses should include a freshness marker so the frontend knows how recent
  the data is.

## My usage so far
The work so far is a planning and documentation pass for `Application_Vue/`, based on the
Intern Training learning record.

### What exists now
- `Application_Vue/README.md` — this implementation document
- `Application_Vue/.md` — Vue.js reference notes kept from the existing workspace notes
- `Application_Vue/client/` — placeholder for the Vue frontend
- `Application_Vue/server/` — placeholder for the Flask backend

### What has been decided
- The application domain and feature set
- The stack and architecture
- The 8 principles that should guide implementation
- The intended usage of database, SQL, and API concepts
- The implementation order and the future file layout

### What still needs to be built
- The Flask backend with order and sales models and endpoints
- The Vue frontend with order creation, listing, status tracking, and reports
- PostgreSQL schema, constraints, and indexes
- The business rules for validation, totals, statuses, and duplicate detection
- The sales report queries and their API exposure

## Files and folders expected now
These are the files and folders the project already has or should have at the start.

### Root
- `README.md` — this document
- `.md` — Vue.js reference notes

### Frontend
- `client/` — Vue.js application
  - expected entry point and component tree for order management and reports
  - expected API service layer or composables for calling the backend
  - expected state management for orders, filters, and report views

### Backend
- `server/` — Flask application
  - expected application factory
  - expected configuration from `.env`
  - expected routes for orders and reports
  - expected services for business rules and SQL
  - expected database layer for connections and transactions
  - expected shared validators and shared query/report builders
  - expected error handling and logging setup

## Files and folders planned for future implementation
These are the files and folders expected to be created as the project grows.

### Backend planned files
- `server/.env` and `.env.example` — secrets and configurable settings
- `server/config.py` — fail-fast configuration
- `server/app.py` — application factory, routes, error handlers
- `server/wsgi.py` — production entrypoint
- `server/init_db.py` — one-time schema setup
- `server/database/connection.py` — connection pool and transaction context managers
- `server/database/schema.py` — DDL for orders, customers, products, order lines, statuses
- `server/services/order_service.py` — order creation, totals, status transitions
- `server/services/customer_service.py` — customer lookups and validation
- `server/services/product_service.py` — product lookups and pricing context
- `server/services/report_service.py` — product-wise and date-wise sales aggregation
- `server/routes/order_routes.py` — HTTP handling for orders
- `server/routes/report_routes.py` — HTTP handling for sales reports
- `server/utils/validation.py` — shared input validators
- `server/utils/query_filters.py` — shared filter and ordering builders
- `server/utils/logger.py` — bounded rotating logging
- `server/errors.py` — shared exception types and mappings

### Database planned objects
- customers table
- products table
- orders table
- order_lines table
- order status history or status transition rules
- indexes for listing, filtering, and reporting
- possibly an idempotency or duplicate-tracking aid if retries are supported

### Frontend planned files
- `client/` Vue project structure
- order creation and edit views
- order list view with filters and status display
- order detail view
- sales report views for product-wise and date-wise breakdowns
- shared API client or service module
- shared state for orders, filters, and report parameters

### Cross-cutting planned concerns
- transactions for order creation and status changes
- centralized validation at the API boundary
- centralized error handling and logging
- bounded pagination and report queries
- documented duplicate-order rules and status transition rules
- tests for validators, services, and main route flows where applicable

## Implementation order
1. Lock the feature set and the API contract
2. Define duplicate-order rules, status transitions, required fields, and total calculation
3. Set up the Flask application factory, configuration, and database layer
4. Create the PostgreSQL schema and indexes
5. Implement order creation, listing, and detail endpoints
6. Implement validation, totals, and status transitions in services
7. Implement duplicate detection in the backend
8. Build the Vue client for create, list, detail, and status workflows
9. Add product-wise and date-wise sales reports
10. Add shared validators, shared query builders, logging, and error handling
11. Add tests for the core backend paths where applicable
12. Polish UI state management with Vue reactivity and filters

## Decisions to make before building endpoints
- What makes an order a duplicate in your rules
- Which order statuses exist and which transitions are allowed
- Which fields are required at order creation time
- How order totals are calculated from line items
- Whether reports should be live queries or cached/async
- How pagination and report boundedness should work

## Notes
- The repo root is `F:/Intern_Training/` per the git working tree.
- This workspace uses Git Bash on Windows. POSIX commands are expected.
- This README replaces the previous `Application_Vue/README.md` and is written as
  implementation documentation from the reviewed Intern Training learning.

## Next Steps
- Initialize the Vue client in `client/`
- Initialize the Flask server in `server/`
- Configure PostgreSQL connection and migrations
- Define the order and report API contract
- Implement order validation, totals, status tracking, duplicate detection, and sales reports
