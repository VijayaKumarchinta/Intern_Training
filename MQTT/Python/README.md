# Paho MQTT Client in Python

One demo script, [mqttdemo.py](mqttdemo.py), plus my notes in
[python_Learning.md](python_Learning.md).

## What mqttdemo.py does

A single `MQTTClient` class that connects to a TLS-enabled Mosquitto broker and
runs the full publish/subscribe round trip:

```text
connect → on_connect → subscribe → on_subscribe → publish
        → on_publish → on_message → loop_forever → Ctrl+C → finally → disconnect
```

The pieces worth noticing:

- **Callback API v2** — `mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, ...)`.
  On Paho 2.x you must ask for it explicitly; the default is the legacy API.
- **TLS on port 8883** — `tls_set()` with CA, client cert and client key, plus
  `username_pw_set()`. Broker side is configured in `mosquitto.conf` (see
  [../Learning.md](../Learning.md)); both sides must agree or you get an
  `SSLCertVerificationError`.
- **All five callbacks** — on_connect / on_message / on_publish / on_subscribe
  / on_disconnect, each wrapped in its own try/except with
  `logging.exception()`.
- **Return-code checks** — the immediate return of `subscribe()`
  (`result, mid`) and `publish()` (`result.rc`) are checked against
  `mqtt.MQTT_ERR_SUCCESS`. That is different from the later callbacks: the
  return value tells you whether the *request* was accepted, the callbacks tell
  you what the broker did with it.
- **Logging** — normal runs at `INFO` (paho's own logger enabled via
  `enable_logger()`); drop to `DEBUG` when you want to see raw packets.
- **Safe shutdown** — `disconnect()` checks `is_connected()` first, and
  `main()` uses `finally` so cleanup happens even after an exception.

## Honest note on the demo flow

`on_subscribe()` publishes a fixed `"Hello, MQTT!"` message. That is a demo
choreography, not production design — a real IIoT client would subscribe to
device topics and process whatever arrives. It was the clearest way to watch
all five callbacks fire in one run.

## Running it

1. Start Mosquitto with a TLS listener on 8883 (cert setup in
   [../Learning.md](../Learning.md)).
2. Fix the hard-coded cert paths in `__init__` if yours differ.
3. `python mqttdemo.py`, then stop with Ctrl+C.

---
Back to the [MQTT folder](../README.md) · [repository guide](../../README.md).
