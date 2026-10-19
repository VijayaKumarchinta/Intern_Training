# Order & Sales Management — Implementation Review

Reviewed against `SPEC.md` (source of truth), the Flask routes, the Vue views and the test suite.
The dashboard design experiments were reverted at the user's request; this document now covers the
endpoint inventory and the review findings only. Status: **78/78 backend tests pass**,
`npm run build` passes.

---

## 1. API endpoints actually exposed

All routes are registered in `server/app/__init__.py`. "Auth" means any verified user.

### Authentication — `/api/auth`

| Method | Endpoint | Access | Purpose | Requirement |
|---|---|---|---|---|
| POST | `/register` | Public | Create a customer account. Forces `role=customer`, requires an existing unlinked `customer_id` whose email matches (when present), sends a 6-digit OTP. | Registration |
| POST | `/verify` | Public | Verify the OTP (2 min TTL, 3 attempts). Optional `customer_id` links the profile to the account at the same moment. | Email verification |
| POST | `/resend-verification` | Public | Re-issue a fresh OTP; always returns a generic message. | Verification |
| POST | `/login` | Public | Credentials → JWT (12 h) + user. Generic `401` for bad credentials and unverified accounts. | Login |
| POST | `/forgot-password` | Public | Same response for known/unknown emails; stores a 1-hour reset token. | Password reset |
| POST | `/reset-password` | Public | Token + new password; bumps `token_version`, revoking existing JWTs. | Password reset |
| GET | `/me` | Auth | Current user, role, and linked customer. | Session / RBAC |

### Orders — `/api/orders`

| Method | Endpoint | Access | Purpose | Requirement |
|---|---|---|---|---|
| GET | `/` | Auth | Paginated list. Admin sees all, customer sees only their linked customer. Filters: `status`, `customer_id`, `page`, `per_page` (max 200). Each row includes computed `total` + `item_count`. | Order tracking, ownership |
| GET | `/<order_id>` | Auth | Order detail with line items and total. Customers get `404` for other customers' orders (no ID leak). | Ownership |
| POST | `/` | Admin | Validate payload, insert header + items atomically, price taken from `products.current_price`, status forced to `Pending`. | Create order, totals, validation |
| PATCH | `/<order_id>/status` | Admin | Status change with transition rules (e.g. `Shipped → Delivered/Returned`). | Status tracking |
| GET | `/duplicates` | Admin | Groups sharing customer + product + quantity + price + date, with the order IDs involved. | Duplicate detection |

### Customers — `/api/customers`

| Method | Endpoint | Access | Purpose | Requirement |
|---|---|---|---|---|
| GET | `/` | Admin | Every customer record (no pagination). | Customer management |
| POST | `/` | Admin | Create a customer record (`customer_id`, `cust_name`, optional email). | Customer management |

### Products — `/api/products`

| Method | Endpoint | Access | Purpose | Requirement |
|---|---|---|---|---|
| GET | `/` | Auth | Full catalogue with `current_price`. | Order creation, reports |
| POST | `/` | Admin | Create product; duplicate names rejected. | Catalogue |
| PATCH | `/<product_id>` | Admin | Update `current_price`. | Server-side pricing |
| DELETE | `/<product_id>` | Admin | Delete only when the product has no order items (`409` otherwise). | Catalogue integrity |

### Reports — `/api/reports`

| Method | Endpoint | Access | Purpose | Requirement |
|---|---|---|---|---|
| GET | `/summary` | Admin | Dashboard aggregate: revenue, sale orders, units, awaiting action, 5 latest orders, 3 duplicate samples, product breakdown, monthly breakdown. | Dashboard |
| GET | `/product-wise` | Admin | Product-wise items/units/revenue, sale statuses only. `?format=csv` downloads. | Product-wise report |
| GET | `/date-wise` | Admin | Date-wise orders/units/revenue, `?group=day\|month`, `?format=csv`. | Date-wise report |

### Health

`GET /` and `GET /health` return `{"status":"ok"}`.

### Endpoints in the spec that are **not** implemented

| Missing endpoint | Impact |
|---|---|
| `POST /api/orders/validate` | No server-side dry-run; the Create Order form can only discover errors by attempting an insert. |
| `POST /api/import/orders` | CSV import exists only as `db/load_data.py`, not as an admin API. The import → staging → reconcile flow from the spec is not exposed. |
| `PATCH /api/customers/<id>/link` | Admins cannot link an existing account to a customer profile. Linking only happens during `/auth/verify`, which contradicts spec §7.5. |

Also note the naming drift: the README lists `/api/reports/product-sales`, `/daily-sales`,
`/monthly-sales`; the code (correctly, per `SPEC.md`) exposes `/product-wise` and
`/date-wise?group=`.

---

## 2. Review findings

### High priority

1. **Customer linking bypasses the admin rule.** `link_customer()` is called from `/auth/verify`
   with a `customer_id` supplied by the registrant. The email check only applies when the customer
   row already has an email; imported customers often have `NULL`, so anyone who knows a customer ID
   can claim it at verification. Spec §7.5 requires an admin to perform the link.
   Add `PATCH /api/customers/<id>/link` (admin-only), remove linking from `/verify`, and require an
   explicit admin action for imported profiles.
2. **Customers cannot create their own orders.** `POST /api/orders` is admin-only, and
   `tests/test_permissions.py` asserts `403` for customers. README §7.6/§11 says a customer may
   create an order for their own profile. Decide which is correct; if customers may order, add an
   ownership-scoped branch and tests.
3. **`POST /api/orders` returns `400` for unexpected failures.** `routes/orders.py` catches every
   `Exception` and answers `400 "Failed to create order"`. A database outage should be `500`
   without leaking internals; log and return `500`.
4. **N+1 queries in the order list.** `list_orders` computes `sum(i.quantity * i.unit_price)` per
   row after a lazy load — roughly `2n+1` queries for `per_page=50`. Aggregate in SQL (or
   `selectinload(Order.items)`) before this dataset grows.
5. **Duplicate groups have no resolution path.** They are detected and displayed, but there is no
   dismiss/merge/confirm endpoint. Spec says "flag for admin review", so at minimum record review
   state (or document that the page is read-only on purpose).

### Medium priority

6. **`GET /api/customers` ignores pagination** although `SPEC.md` marks it paginated; the UI works
   around it with `customers.slice(0, 50)`, silently hiding the rest.
7. **`get_dashboard_summary()` duplicates report queries** (product and monthly blocks repeat
   `product_wise_report()`/`date_wise_report()`). Reuse the service functions so the dashboard cannot
   drift from the CSV reports.
8. **`validate_order_payload()` validates `order_status`, then `create_order` forces `Pending`.**
   Harmless but misleading; drop the check or honour an explicit initial status if business rules
   allow it.
9. **No status history.** Spec marks it optional, but "track order statuses" is easier to audit with
   `order_status_history` written in the same transaction as `PATCH`.
10. **Deprecated ORM call**: `Customer.query.get()` in `routes/customers.py`; use
    `db.session.get(Customer, ...)`. Unused imports (`auth_required`, imported `email` value).
11. **Import pipeline is a script, not an API.** `db/load_data.py` is not covered by tests; the
    reconciliation report promised by the spec is not produced anywhere visible.

### Frontend issues

| # | Issue | Status |
|---|---|---|
| 1 | Dashboard fetches `latest_orders` and `duplicate_groups` but never renders them — actionable payload is discarded. | Open |
| 2 | Hardcoded "Good afternoon" greeting; the dashboard is titled "Reports". | Open |
| 3 | Fixed 4-column grid, 88px icon-only sidebar and 48px padding cause **504px of horizontal overflow at 390px**. | Open |
| 4 | No per-status pipeline or drill-down from "Awaiting action". | Open |
| 5 | `CreateOrder.vue` supports one line item only, contradicting multi-product orders. | Open |
| 6 | `OrderDetail.vue` shows `product_id`, not product name; `allowedTransitions[status].length` throws on an unexpected status; reads `localStorage` instead of the auth store. | Open |
| 7 | `Orders.vue` shows `customer_id` only, no search/date filter/export. | Open |
| 8 | `Customers.vue` silently slices to 50 rows and has no "link user" action. | Open |
| 9 | `Duplicates.vue` shows raw IDs with no links or names; no resolution action. | Open |
| 10 | `--accent-blue` is used but never defined, so links fall back to the inherited colour. | Open |
| 11 | Vue Router guard still calls `next()` (deprecation warning R0025). | Open |
| 12 | Plain-text loading states, `alert()`/`confirm()` for errors, no retry. | Open |

### Recommended next steps

Close the three spec gaps first — admin customer linking, order validation, CSV import — then fix the
order form (multi-item + totals) and the N+1 in the order list. Frontend polish should follow the
backend contract rather than precede it.
