# Intern_Training — OrderSalesManagement Documentation Pack

This package contains the current, code-written documentation for the Order & Sales Management application.

- `endpoints_explained.md` — every HTTP endpoint, methods, URLs, request/response shape, status codes, and backend enforcement.
- `frontend_files_explained.md` — every frontend file, its route/component role, state, and where it connects to the backend.
- `frontend_backend_communication.md` — the exact request path: Vite proxy → Flask route → service → DB → response.
- `backend_files_explained.md` — every Python backend file: app factory/config/extensions/models, routes, services, utils, and the pytest suite.
- `final_full_project_explained.md` — integrated explanation: stack, architecture, data model, flows, status machine, reports, security model, test count.

All paths are relative to the repository root `Order_Sales_Management/`.

## Quality check

- Backend dependency resolution: passed.
- Backend test suite: `python -m pytest tests/ -q` → **84 passed**.
- No client-side build or live API ran in this environment (no local database process and no browser), so frontend runtime behavior and DB integration are not covered by an automated check here.
