# Paho MQTT Client (mqttdemo.py) Concepts — Intern Training

**Source:** `MQTT/Python/mqttdemo.py`

> One MQTTClient class where `__init__` sets everything up (broker, port, topic, msg, client_id, tls certs, callbacks) so the methods stay small. A complete pub/sub round trip over TLS.

---

## 1. Paho client basics

**Till paho 2.x the callback API defaulted to version 1**, since the 2.0 release we have to assign it ourselves to version 2 explicitly, otherwise we silently get the legacy API.

```python
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="P1")
```

**Pros:**
- Full pub/sub round trip in Python with TLS + auth.
- Complete five-callback coverage.

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

## 2. The five callbacks

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

## 3. Demo choreography

`on_connect()` calls `subscribe()` and `on_subscribe()` calls `publish()`, so all five callbacks fire in one run and the subscriber gets the ack from the server before the publish; a demo flow on purpose. A real IIoT client would subscribe to device topics and process whatever arrives.

**Pros:**
- Shows the full round trip in a single run.

**Cons/drawbacks:**
- Not a realistic production flow; a real client subscribes to device topics and processes whatever arrives.

**Use cases:**
- Learning and proof-of-concept.

**Usage:**
- Follow the demo order: connect → subscribe → publish → message handler.

---

## 4. Loops — `loop_forever()` vs `loop_start()`

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

## 5. Return codes vs callbacks — both checks matter

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

## 6. Error types encountered

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

## 7. Message handling side

| Function / attribute | What it does |
|---|---|
| `message.payload.decode("utf-8")` | bytes to string, with the `UnicodeDecodeError` fallback |
| `message.topic` | which topic the msg came in on |

**Pros:**
- Safe payload decoding with a fallback.

**Cons/drawbacks:**
- `UnicodeDecodeError` requires explicit fallback.

**Use cases:**
- Processing incoming MQTT payloads in Python.

**Usage:**
```python
try:
    payload = message.payload.decode("utf-8")
except UnicodeDecodeError:
    payload = repr(message.payload)
```

---

## 8. Logging side

| Function | What it does |
|---|---|
| `logging.getLogger(__name__)` | the named logger per module |
| `logging.basicConfig(level, format)` | the one-time setup in `__main__` |
| `logger.exception("...")` | logs the message WITH the full traceback, used in every except block |
| `logger.info("...")` | the normal flow messages |

**Pros:**
- One named logger per module; exception context captured automatically.

**Cons/drawbacks:**
- `logger.exception()` only works inside an `except` block.

**Use cases:**
- Any Python service.

**Usage:**
- Use `logger.exception()` in every `except` block; `logger.info()` for normal flow.

---

## 9. Key functions used throughout

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

---

**Quick reference — all MQTT/Python files**
| File | Role |
|---|---|
| mqttdemo.py | Paho MQTTClient demo |

**Status:** Practiced end-to-end (broker + TLS/mTLS + Paho + all five callbacks).
