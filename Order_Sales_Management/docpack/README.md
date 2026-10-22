# Intern_Training — OrderSalesManagement Documentation Pack

This package contains four Markdown files generated from `Order_Sales_Management/`:

1. `frontend_files_explained.md` — every frontend file, with its lines, functions, consts, and template/component roles.
2. `endpoints_explained.md` — every HTTP endpoint, methods, URLs, request/response shape, status codes, and backend enforcement.
3. `backend_files_explained.md` — every Python backend file, with functions, classes, constants, classes, and database logic.
4. `final_full_project_explained.md` — the complete integrated explanation of the app: stack, architecture, data model, flows, status machine, reports, security model, and where each piece lives.

All paths are relative to the repository root `Order_Sales_Management/`.

## How this was generated

Source files inspected:

- `server/app/__init__.py`, `server/app/config.py`, `server/app/constants.py`
- `server/app/extensions.py`, `server/app/models.py`
- `server/app/utils/decorators.py`, `server/app/utils/permissions.py`, `server/app/utils/email.py`, `server/app/utils/validators.py`
- `server/app/services/auth_service.py`, `server/app/services/order_service.py`
- `server/app/routes/auth.py`, `server/app/routes/customers.py`, `server/app/routes/orders.py`
- `server/app/routes/products.py`, `server/app/routes/reports.py`, `server/app/routes/users.py`
- `client/src/main.js`, `client/src/router/index.js`, `client/src/services/api.js`
- `client/src/stores/auth.js`, `client/src/stores/summary.js`, `client/src/utils/format.js`
- `client/src/style.css`, `client/vite.config.js`
- 15 Vue views/components/layouts: `Landing`, `Login`, `Register`, `ForgotPassword`, `ResetPassword`, `MyOrders`, `Orders`, `CreateOrder`, `OrderDetail`, `Reports`, `Customers`, `Products`, `Duplicates`, `Users`, `Totals`, `Icon`, `AuthShell`, `AppLayout`

Quality check run on the backend before generation:

- Dependency resolution: passed.
- Backend test suite: `python -m pytest tests/ -v` through the project virtualenv → **82 passed** (authentication, permissions, pricing, reports, order workflow, smoke).
- No client-side build or live API ran in this environment (no local database process and no browser), so frontend runtime behavior and DB integration are not covered by an automated check here.

## File and line reference

Each section lists the source path so the explanation can be located in the real repository. The files below are the documentation pack only; the source code is untouched.
