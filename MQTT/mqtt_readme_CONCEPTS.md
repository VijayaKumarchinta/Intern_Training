# MQTT (Broker + TLS/mTLS + Paho) Concepts — Intern Training

**Source:** `MQTT/mqtt_readme.md`

> MQTT - a lightweight, low bandwidth message queuing transport where it uses pub/sub to deliver the messages.

- **publisher** - the client that sends a msg to a topic
- **subscriber** - the client that receives a msg from a topic
- **broker** - a server where it sends/receives msgs from/to the clients, nobody talks directly, the broker stands in the middle
- **topic** - the channel name the msgs travel on, pub and sub must point at the same one

---

## 1. Broker basics — how mosquitto was run on Windows

**What:** The MQTT broker (Mosquitto) running as a Windows service.

**Common commands:**
- `net start mosquitto` — starts the broker as a Windows service.
- `mosquitto -c mosquitto.conf` — runs it in the foreground with the conf file.
- `net stop mosquitto` — stops the service (or Ctrl+C for the foreground run).
- `net stop mosquitto && net start mosquitto` — the restart, needed after every conf edit.

**Default install files** — `mosquitto.conf` and the certs live in `C:/Program Files/Mosquitto/`; edit the conf as admin and save, never generate it with `echo` (it erases the new lines — a real bug hit, documented).

**Connection limits:**
- `max_connections` — total connections allowed per listener (one port).
- `global_max_connections` — total connections allowed per broker (all listeners together).
- `global_max_clients` — how many devices the broker can remember.

**Pros:**
- Lets you control how many clients the broker accepts.
- Connection limits prevent a single client from exhausting the broker.

**Cons/drawbacks:**
- Too-low limits reject legit clients (reason code 9 — quota exceeded).
- Manual config management on Windows.

**Errors encountered & causes:**
- `ConnectionRefusedError` — broker not running / wrong port.

**Use cases:**
- Local development, multi-site setups, device gateways.

**Usage:**
- Start as a service, edit config as admin, restart after every conf change.

---

## 2. TLS/mTLS — the full certificate chain built with openssl

**Why:** Plain MQTT sends everything readable on the wire; TLS encrypts it, mTLS makes both sides prove who they are.

**What each file is for:**
- `ca.key` — the CA private key, created encrypted with `-des3` (self-signed root).
- `ca.crt` — the CA certificate, signs both server and client certs and verifies both sides.
- `server.key` / `server.csr` / `server.crt` — the broker identity; the CSR carries CN=ip_or_domain.
- `client.key` / `client.csr` / `client.crt` — the client identity; the CSR carries CN=client1; with `use_identity_as_username=true` the CN becomes the username (client1).

**Commands in order:**
1. `openssl genrsa -des3 -out ca.key 2048` — creates the encrypted CA key.
2. `openssl req -new -x509 -out ca.crt -key ca.key -days 365` — creates the CA cert from that key.
3. `openssl genrsa -out server.key 2048` — server key for the broker.
4. `openssl req -new -out server.csr -key server.key -subj "/CN=domain"` — server CSR; `-subj` skips interactive prompts.
5. `openssl x509 -req -out server.crt -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -extfile san.cnf -extensions v3_req` — signs the server cert with the CA; `-CAcreateserial` makes the `.srl` file openssl uses to track our CA; SAN comes from `san.cnf`.
6. `openssl genrsa -out client.key 2048` — client key.
7. `openssl req -new -out client.csr -key client.key -subj "/CN=client1"` — client CSR.
8. `openssl x509 -req -out client.crt -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 360` — signs the client cert.

**`-subj` flag works for BOTH server and client CSRs**, format `" /C=IN/ST=State/L=City/O=Org/CN=identity "` (CN is must at least), essential for scripting certs for multiple clients.

**When the IP changes (different wifi router)** — no need to regenerate everything, just add the new IP in `san.cnf` and regenerate `server.crt`; that is why the SAN entry saves you.

**Pros:**
- Mutual authentication: both client and server prove identity.
- Encryption in transit.

**Cons/drawbacks:**
- OpenSSL 3.x **requires** SAN on the server cert — without it, certificate verification fails.
- If server/client don't agree on conf paths + port, you get `SSLCertVerificationError`.

**Errors encountered & causes:**
- `ssl.SSLCertVerificationError` — cert without SAN, wrong CN, expired, or server/client config mismatch.
- `ConnectionRefusedError` — broker not running / wrong port.

**Use cases:**
- Any service needing encrypted + authenticated transport (MQTT broker, API clients, web servers).

**Usage:**
```bash
openssl genrsa -des3 -out ca.key 2048
openssl req -new -x509 -out ca.crt -key ca.key -days 365
openssl genrsa -out server.key 2048
openssl req -new -out server.csr -key server.key -subj "/CN=domain"
openssl x509 -req -out server.crt -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -extfile san.cnf -extensions v3_req
openssl genrsa -out client.key 2048
openssl req -new -out client.csr -key client.key -subj "/CN=client1"
openssl x509 -req -out client.crt -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 360
```

---

## 3. SAN — subject alternative name (san.cnf)

**What:** An extra field in the server certificate listing every IP/domain the server accepts connections on. OpenSSL 3.x REQUIRES it — without SAN the certificate verify simply fails.

`san.cnf`:
- `[v3_req]` — the section for X.509 v3 extensions
- `subjectAltName = @alt_names` — the field, pointing at the `[alt_names]` section
- `IP.1` / `IP.2` — the valid IP addresses (10.58.166.132 and 127.0.0.1)
- `DNS.1 = localhost` — the valid domain name

**Rule learned:** with an IP in the SAN, a new IP only needs a `san.cnf` edit + `server.crt` regen; with a domain/localhost the same idea applies. Either way, the CA and client certs never change.

**Pros:**
- Certificates work across changing network addresses.

**Cons/drawbacks:**
- Without SAN, OpenSSL 3.x refuses to verify.

**Errors encountered & causes:**
- `ssl.SSLCertVerificationError` — cert without SAN.

**Use cases:**
- Any server certificate that must match multiple IPs/domains.

**Usage:**
- Create `san.cnf` with `subjectAltName = @alt_names`, `IP.1`, `IP.2`, `DNS.1`, then sign with `-extfile san.cnf -extensions v3_req`.

---

## 4. mosquitto.conf — the real TLS listener

**Where:** `C:/Program Files/Mosquitto/mosquitto.conf`, edited as admin, certs stored in the same install folder.

**The conf:**
- `listener 8883` — the TLS port (8883 is the default for MQTT over TLS).
- `cafile` — the CA cert, verifies both server and client.
- `certfile` — the server cert, proves the broker identity.
- `keyfile` — the server private key for the handshake.
- `require_certificate true` — forces every client to present a cert (mTLS).
- `use_identity_as_username true` — takes the CN from the client cert as the username.
- `allow_anonymous false` — rejects clients without a valid cert.
- `password_file` — NOT needed when `require_certificate` is on, the cert is the identity.

**Server side and client side must agree** — the conf paths on the server, the `tls_set` paths on the Python client, and the same port 8883 on both, or you get an `SSLCertVerificationError`. `ca.crt` also has to be placed in the Windows Trusted Root Certification Authorities store so the system trusts our CA.

**Pros:**
- mTLS gives real mutual authentication without a password file.

**Cons/drawbacks:**
- Certificate and conf management is manual; managing many clients is a chore.

**Errors encountered & causes:**
- `SSLCertVerificationError` — server/client conf paths disagree, or ca.crt not trusted.

**Use cases:**
- Production MQTT brokers with TLS/mTLS.

**Usage:**
- Set `listener 8883`, `cafile`, `certfile`, `keyfile`, `require_certificate true`, `use_identity_as_username true`, `allow_anonymous false`.

---

## 5. Testing through the terminal

```bash
mosquitto_sub --cafile ca.crt --cert client.crt --key client.key -h 10.58.166.132 -p 8883 -t test
mosquitto_pub --cafile ca.crt --cert client.crt --key client.key -h 10.58.166.132 -p 8883 -t test -m "hello there"
```

- Always send messages through `--cafile/--cert/--key`; a plain connect is refused by the listener.

**Pros:**
- Quick hands-free verification of the broker TLS/mTLS setup.

**Cons/drawbacks:**
- Tedious for repeated scripted testing; use Paho for that.

**Errors encountered & causes:**
- `ConnectionRefusedError` — broker not running / wrong port.

**Use cases:**
- Verifying the broker config, testing client certs, CI smoke tests.

**Usage:**
- Run the two commands above; both must use the same cert trio and port 8883.

---

## 6. Python client — paho (mqttdemo.py)

**Till paho 2.x the callback API defaulted to version 1**, since the 2.0 release we have to assign it ourselves to version 2 explicitly, otherwise we silently get the legacy API.

One `MQTTClient` class where `__init__` sets everything up (broker, port, topic, msg, client_id, tls certs, callbacks) so the methods stay small.

**Demo choreography** — `on_connect()` calls `subscribe()` and `on_subscribe()` calls `publish()`, so all five callbacks fire in one run and the subscriber gets the ack from the server before the publish; a demo flow on purpose. A real IIoT client would subscribe to device topics and process whatever arrives.

**Pros:**
- Complete pub/sub round trip in Python with TLS + auth.
- Full five-callback coverage.

**Cons/drawbacks:**
- Callback API version 2 must be set explicitly or you silently get v1.

**Errors encountered & causes:**
- Callbacks "not firing" — expecting callbacks to *replace* return-code checks → check `subscribe()`/`publish()` results **and** register callbacks.

**Use cases:**
- Python-based MQTT publishers/subscribers, IoT device gateways.

**Usage:**
```python
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="P1")
client.enable_logger()
client.tls_set(ca_certs="ca.crt", certfile="client.crt", keyfile="client.key")
client.username_pw_set("user", "userpass")
client.connect(host, 8883)
client.subscribe("factory/site/M102/telemetry")
client.loop_forever()
```

---

## 7. The five callbacks

**What:** Predefined functions we register; Paho runs them automatically.

| Callback | What it does |
|---|---|
| `on_connect(client, userdata, flags, reason_code, properties)` | runs whenever the connection happens; checks `reason_code.is_failure` then subscribes |
| `on_subscribe(client, userdata, mid, reason_codes, properties)` | ack from the server for the subscribe; then triggers the publish |
| `on_publish(client, userdata, mid, reason_code, properties)` | ack that the publish went out |
| `on_message(client, userdata, message)` | runs whenever a msg arrives; decodes `message.payload` and logs topic + payload |
| `on_disconnect(client, userdata, disconnect_flags, reason_code, properties)` | runs when the connection drops |

**Every callback is wrapped in its own try/except with `logging.exception`** so one bad callback never kills the loop silently.

**Pros:**
- Decouples broker acks from the app logic.

**Cons/drawbacks:**
- If one callback raises, it can silently stop the loop unless wrapped in try/except.

**Errors encountered & causes:**
- Callbacks "not firing" → developer expected callbacks to *replace* return-code checks.

**Use cases:**
- Any real-time handler that reacts to broker events.

**Usage:**
- Register all five, wrap each in try/except with `logging.exception`, check `subscribe()`/`publish()` return codes as well.

---

## 8. Loops — how the MQTT communication runs in the background

| Function | What it does |
|---|---|
| `loop_forever()` | blocks the main thread, keeps the connection alive and reconnects automatically; use it when we only do pub/sub |
| `loop_start()` | runs the loop on a background thread; use it when we manage multiple clients |
| `connect()` | opens the TCP connection; the loop then keeps it alive while the callbacks do their work |

**Pros:**
- `loop_forever()` auto-reconnects; `loop_start()` lets you manage multiple clients.

**Cons/drawbacks:**
- `loop_forever()` blocks the main thread.

**Errors encountered & causes:**
- Expecting callbacks to replace return-code checks → both are needed.

**Use cases:**
- Use `loop_forever()` for a single client; `loop_start()` when managing multiple clients.

**Usage:**
```python
client.loop_forever()   # single client
client.loop_start()     # multiple clients
```

---

## 9. Return codes vs callbacks — both checks matter

| What | What it answers | Example |
|---|---|---|
| `subscribe()` return value | "did my request go out" — returns `(res, mid)`, checked against `mqtt.MQTT_ERR_SUCCESS` | `res, mid = client.subscribe("topic")` |
| `publish()` return value | "did my request go out" — returns an object with `.rc` | `rc = client.publish("topic", msg).rc` |
| Callbacks (`on_connect`, `on_subscribe`, `on_publish`) | "what did the broker actually do" | `on_connect` checks `reason_code.is_failure` |

**Pros:**
- Full visibility of both the request and the broker's confirmation.

**Cons/drawbacks:**
- Easy to confuse the two; only one is checked.

**Errors encountered & causes:**
- Callbacks "not firing" → expecting callbacks to replace return-code checks.

**Use cases:**
- Any production MQTT client where delivery confirmation matters.

**Usage:**
- Always check `subscribe()`/`publish()` return codes **and** register callbacks.

---

## 10. Error types encountered

| Error | Meaning |
|---|---|
| `ConnectionRefusedError` | broker not running / wrong port |
| `ssl.SSLCertVerificationError` | expired/unmatched cert or key files, or server/client don't agree |
| reason_code 0 | connection success |
| 1 | unacceptable protocol version |
| 2 | identifier rejected, client_id not acceptable |
| 3 | server unavailable |
| 4 | bad username/password |
| 5 | not authorized |
| 7 | alternative authentication required |
| 8 | flow control — sending too fast |
| 9 | quota exceeded, too many connections |
| 14 | server error, internal error |
| `MQTT_ERR_NO_CONN` / `MQTT_ERR_PROTOCOL` | protocol errors on the wire |
| `MQTT_ERR_SUCCESS` | success return code for sub/pub |
| `UnicodeDecodeError` | payload is not UTF-8; fall back to `repr(message.payload)` |

**Enabling the paho logger (`enable_logger`)** shows packets in the terminal; drop to DEBUG to watch raw traffic.

**Pros:**
- Complete, observable error taxonomy for MQTT troubleshooting.

**Cons/drawbacks:**
- Many distinct reason codes to memorise; use a lookup table.

**Use cases:**
- Debugging MQTT connectivity in development and production.

**Usage:**
- Check `reason_code.is_failure` after connect; handle each MQTT error code explicitly.

---

## 11. Key functions used throughout

**Broker/openssl side**
- `net start/stop mosquitto` — service control.
- `openssl genrsa / req / x509` — key creation, CSR/cert signing, the whole chain.
- `mosquitto_sub` / `mosquitto_pub` — terminal testing with `--cafile/--cert/--key`.

**Paho side**
- `mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="P1")` — the client object; v2 callbacks asked for explicitly.
- `enable_logger()` — pipes paho's own logs into our logging.
- `tls_set(ca_certs=, certfile=, keyfile=)` — the client side of TLS in one setter.
- `username_pw_set("user", "userpass")` — credentials without the terminal cmd dance.
- `connect(host, port)` — opens the connection to the broker.
- `subscribe(topic)` — returns `(res, mid)`, checked against `MQTT_ERR_SUCCESS`.
- `publish(topic, msg)` — returns an object with `.rc`, checked the same way.
- `loop_forever()` — the blocking background loop with auto-reconnect.
- `is_connected()` — checked before `disconnect()` so we never disconnect twice.
- `disconnect()` — clean goodbye from the broker.

**Logging side**
- `logging.getLogger(__name__)` — the named logger per module.
- `logging.basicConfig(level, format)` — the one-time setup in `__main__`.
- `logger.exception("...")` — logs the message WITH the full traceback, used in every except block.
- `logger.info("...")` — the normal flow messages.

**Message handling side**
- `message.payload.decode("utf-8")` — bytes to string, with the `UnicodeDecodeError` fallback.
- `message.topic` — which topic the msg came in on.

---

## 12. Where it leads — Machine_Sensor_API

The capstone of this folder, a Flask + PostgreSQL API for machines and sensor readings with bulk import of MQTT snapshot pickles; it uses the same pub/sub thinking, honest status codes, and TLS habits end to end. Code lives in `Machine_Sensor_API/`.

---

## 13. Not used yet — next to learn

- **QoS levels in practice** — 0 at most once, 1 at least once, 2 exactly once; the demo runs on the default.
- **Retained messages** — the broker keeps the last message on a topic for new subscribers.
- **Last will and testament** — the broker announces a client that died unexpectedly.
- **Persistent sessions** — queueing messages for a disconnected subscriber.
- **MQTT 5 properties/features** — the properties parameter the callbacks already receive but never use.

---

**Quick reference — all MQTT files**
| File | Role |
|---|---|
| mqtt_readme.md | Broker, TLS/mTLS, Paho client notes |
| Python/mqttdemo.py | Paho MQTT client demo |

**Status:** Practiced end-to-end (broker + TLS/mTLS + Paho + terminal testing).
