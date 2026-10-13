# Order and Sales Management Application

A full-stack application that simulates the order processing and sales operations of a retail / e-commerce business.

## Stack
- Frontend: Vue.js
- Backend: Flask
- Database: PostgreSQL

## Architecture
Traditional three-tier architecture is used deliberately because the application
needs explicit business rules, duplicate order handling, transactional order
processing, and sales reporting.

```
Vue.js  ->  Flask  ->  PostgreSQL
(frontend) (backend)  (database)
```

Alternatives considered:
- Backend-as-a-service (for example Supabase): simpler to start, but hides the
  backend engineering concepts this project is meant to exercise.
- Browser storage (localStorage): useful for offline features, but not suitable
  for shared transactional order data.

## Features
- Manage customer orders
- Validate order details
- Calculate order totals
- Track order statuses
- Identify duplicate orders
- Generate product-wise and date-wise sales reports

## Project Structure
- `client/` - Vue.js frontend
- `server/` - Flask backend
- Root Vue reference notes: `.md`

## Local Notes
- This workspace uses Git Bash on Windows. POSIX commands are expected.
- The existing `.md` file is preserved as the Vue.js reference notes.

## Next Steps
- Initialize the Vue client in `client/`
- Initialize the Flask server in `server/`
- Configure PostgreSQL connection and migrations
- Implement order validation, totals, status tracking, duplicate detection, and sales reports
