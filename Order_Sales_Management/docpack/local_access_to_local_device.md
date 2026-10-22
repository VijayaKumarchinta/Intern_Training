# How Someone on Another Device Can Access Your Local Instance

This file explains how to let another device (phone, work computer, school network, etc.) reach the `OrderSalesManagement` app when you run it on your own machine.

All paths are relative to `Order_Sales_Management/`.

---

## 1. The short answer

- Frontend: start Vite so the app runs on a local port (default `http://localhost:5173`).
- Backend: start Flask so the API runs on a local port (default `http://127.0.0.1:5000`).
- Other devices need:
  1. The machine’s local network IP address.
  2. Both ports open/firewalled.
  3. A URL like `http://<your-local-ip>:5173` and `http://<your-local-ip>:5000`.

But this project is a **development app**, not a production deployment. Before sharing it outside your own network, understand the limitations below.

---

## 2. Where the app actually runs

### Frontend

- `client/src/main.js` mounts the Vue app.
- `client/vite.config.js` sets up:
  - alias `@` → `client/src`
  - dev server proxy: `/api` → `http://127.0.0.1:5000`
- Vite typically runs on `http://localhost:5173` when you run `npm run dev`.

### Backend

- `server/run.py` creates the Flask app and runs the dev server.
- Internally, Flask binds to `127.0.0.1` by default unless you configure `host`.
- Other devices can reach it at `http://<your-local-ip>:5000`.

### Important: the app connects to PostgreSQL through `DATABASE_URL`

- `server/app/config.py` reads `DATABASE_URL` and uses `DB_SCHEMA` (default `order_sales`) as the PostgreSQL search path.
- PostgreSQL must be reachable from the machine running Flask, not necessarily from the browser.
- If your database is on a different machine, change `DATABASE_URL` to point to that host.

---

## 3. Step-by-step: make a locally-run instance reachable

### Step 1: Find your machine’s local IP address

- **Windows:** `ipconfig` in Command Prompt and look for `IPv4 Address` under your active adapter (usually `192.168.x.x` or `10.x.x.x`).
- **macOS/Linux:** `ipconfig getifaddr en0` (Wi-Fi) or `ip addr` / `hostname -I`.

Use the LAN IP, not `127.0.0.1`.

### Step 2: Start the backend and bind it to the LAN IP

Flask by default binds to `127.0.0.1` (localhost only). On Windows, the natural way to expose it on your LAN is:

- Windows Command Prompt:
  ```cmd
  cd server
  set FLASK_RUN_HOST=0.0.0.0
  python run.py
  ```

- PowerShell:
  ```powershell
  cd server
  $env:FLASK_RUN_HOST = "0.0.0.0"
  python run.py
  ```

- This makes Flask listen on all interfaces, so the LAN IP becomes reachable.

If `run.py` binds only to `127.0.0.1` in future versions, change the dev server start command or the run command to use `FLASK_RUN_HOST=0.0.0.0`.

### Step 3: Start the frontend

```powershell
cd client
npm run dev
```

- Vite runs on `http://localhost:5173` by default (still localhost for you).
- Requests to `/api` are proxied to `http://127.0.0.1:5000`.
- For another device to reach the frontend directly, you must also bind Vite to the LAN IP.

---

## 4. Banner/proxy problem: Vite dev proxy only works for your browser

The dev proxy in `client/vite.config.js` is useful for **your browser only**:

```js
server: {
  proxy: {
    '/api': 'http://127.0.0.1:5000',
  }
}
```

This means:

- Your machine: browser at `http://localhost:5173` → Vite forwards `/api` to `127.0.0.1:5000`.
- Another device: if you open `http://<your-local-ip>:5173`, Vite on the other machine usually cannot use that proxy the same way, because:
  - The proxy is configured for the dev server on your machine.
  - The other device is not running Vite’s dev server process.
  - `${IP}` substitutions do not happen automatically from the application files.

Practical result:

- The frontend on your machine works immediately: `http://localhost:5173`.
- To let another device use the app, point it to the backend API directly, or change the dev proxy and frontend base path so both the UI and API use the LAN IP.

---

## 5. What your other device would open (example)

If your machine’s LAN IP is `192.168.1.25`:

- Backend: `http://192.168.1.25:5000`
- Frontend (if bound to LAN): `http://192.168.1.25:5173`

Vite and Flask both log their bind address when started, so check the console output for the port they actually listen on.

---

## 6. Firewall and network rules

### Windows Firewall

- If you get a firewall prompt, allow Python / Flask through.
- Allow inbound traffic on port `5000` (backend).
- Allow inbound traffic on port `5173` (frontend Vite, if sharing the UI directly).

### Router/router firewall

- Some routers block incoming requests or only allow LAN traffic.
- Cellular/mobile hotspot connections may block port access even if the machine is reachable on the LAN.

### VPNs, proxies, and hosts files

- If the other device uses a VPN, corporate proxy, or hosts file, the request may be routed through a different network interface, which can block access.
- Try from a machine on the same Wi-Fi/LAN to verify basic reachability.

---

## 7. Security and permissions

- This is a development app with:
  - Flask dev server
  - No TLS/HTTPS handling
  - Shared browser storage for JWTs
  - Email verification OTP and reset links printed to dev logs
- Do not expose this setup directly on the public internet or share it beyond a trusted LAN without:
  - HTTPS/TLS
  - Strong secrets and environment-protected keys
  - Rate limiting
  - Proper auth and session management
  - Network-level access restrictions

### Tokens and frontend storage

- `client/src/stores/auth.js` stores the JWT in `localStorage`.
- This is convenient for dev, but it is visible to JavaScript and vulnerable to XSS.
- Frontend guards (`client/src/router/index.js`) are UI-side only; backend decorators are the actual security.

---

## 8. Production-state hardening checklist before external exposure

1. Load environment variables from a secure source (no committed `.env`).
2. Enable HTTPS and strong TLS.
3. Replace Flask’s dev server with a WSGI server (for example Gunicorn or uWSGI) behind a reverse proxy.
4. Replace the Vite dev proxy with proper CORS for your production frontend origin.
5. Use HttpOnly, Secure, SameSite cookies instead of `localStorage` JWTs, and add CSRF protection.
6. Move PostgreSQL to a non-public host and restrict network access.
7. Configure cloud/router firewalls to allow only necessary traffic.
8. Implement rate limiting on login, registration, OTP, and password-reset endpoints.

---

## 9. Verification

- Confirm the backend is listening on the LAN IP:
  - Check the terminal for the Flask bind address.
- From another device, run:
  ```powershell
  Test-NetConnection <your-local-ip> -Port 5000
  curl -I http://<your-local-ip>:5000/health
  ```
- On the frontend side, if you bind Vite to the LAN IP, open:
  ```text
  http://<your-local-ip>:5173
  ```
- If the backend is not configured to listen on the LAN IP, requests will fail at the firewall/proxy level before the Flask app can respond.

---

## 10. Summary

| Thing | Default / dev location | What the other device needs |
|---|---|---|
| Frontend (Vite) | `http://localhost:5173` | Addresses and firewall rules; point to `http://<lan-ip>:5173` if you bind Vite to the LAN |
| Backend (Flask) | API on `http://127.0.0.1:5000` | Open/allow port `5000` and use `FLASK_RUN_HOST=0.0.0.0` so the LAN IP is reachable |
| API communication | `Authorization: Bearer <token>` via `client/src/services/api.js` | Same JWT flow works on other devices once auth is successful |
| Database | `DATABASE_URL` + `DB_SCHEMA=order_sales` (PostgreSQL) | PostgreSQL must be reachable on the network or from the machine running Flask |

---

## 11. Fresh checklist for this exact repo

- [ ] Find your PC’s LAN IP.
- [ ] Start Flask with `FLASK_RUN_HOST=0.0.0.0`.
- [ ] Verify `http://<lan-ip>:5000/health` works from another device.
- [ ] If you want the UI reachable too, bind Vite to the LAN IP and open port `5173`, or update the dev proxy base path.
- [ ] Do not put real credentials in the files you share.

---

## 12. Quick example commands

### Backend on LAN

```powershell
cd Order_Sales_Management/server
$env:FLASK_RUN_HOST = "0.0.0.0"
python run.py
```

### Frontend (local only)

```powershell
cd Order_Sales_Management/client
npm run dev
```

### From another device

```powershell
Test-NetConnection 192.168.1.25 -Port 5000
curl -I http://192.168.1.25:5000/health
```

Replace `192.168.1.25` with your machine’s actual LAN IP.
