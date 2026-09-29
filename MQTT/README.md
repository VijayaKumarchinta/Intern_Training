# MQTT & Mosquitto

Everything from my MQTT track: broker notes, the Python client, and the
Machine Sensor API that finally puts it all together.

```text
Publisher → Broker (Mosquitto) → Subscriber
```

## [Learning.md](Learning.md) — broker side

Working notes on running Mosquitto on Windows:

- start / stop / restart (`net start mosquitto`, `net stop ...`, or `-c mosquitto.conf`)
- connection limits: `max_connections` (per listener),
  `global_max_connections`, `global_max_clients`
- the full TLS/mTLS certificate chain with openssl — CA key + cert, server
  key + CSR + cert, client key + CSR + cert — and what each file is for
- SAN (`san.cnf`): why OpenSSL 3.x refuses to verify without it, and how
  adding an IP there beats regenerating everything when the Wi-Fi (and IP)
  changes
- the resulting `mosquitto.conf` TLS listener on port 8883 with
  `require_certificate true`

## [Python/](Python/README.md) — client side

[mqttdemo.py](Python/mqttdemo.py) is a Paho `MQTTClient` class with callback
API v2, TLS, all five callbacks, paho logging and return-code checks — the
flow is explained in [Python/README.md](Python/README.md).

## [Machine_Sensor_API/](Machine_Sensor_API/readme.md) — where it leads

The capstone of this folder: a Flask + PostgreSQL API for machines and sensor
readings, with bulk import of MQTT snapshot pickles. Start with its
[readme](Machine_Sensor_API/readme.md), or jump straight to
[app.py](Machine_Sensor_API/app.py).

[Machine_Sensor_API.zip](Machine_Sensor_API.zip) is the packaged copy that was
shared over email (includes the ~930 MB of pickle data — it will not attach to
Gmail as-is).

---
Back to the [repository guide](../README.md).
