# Machine Monitor (Vue 3 + TypeScript, live over SSE)

## Run (PowerShell)
```powershell
# 1. backend  (Machine_Sensor_API/)
pip install -r requirements.txt
python init_db.py
python app.py                    # http://localhost:8080  (SSE: /dashboard/stream)

# 2. feed - pick one
python mqtt_subscriber.py        # real: broker over mTLS -> PostgreSQL
python simulate_feed.py          # demo: replays the sample CSV as "now"

# 3. dashboard (dashboard/)
npm install
npm run dev                      # http://localhost:5173  (proxies /dashboard -> :8080)
```
Fill `public/tags.json` (name + unit per tag) to replace tag numbers with names.

## Assumptions to confirm
- MQTT topic's last segment = machine name; payload = JSON `{"ST","TS","VR":[v]}` (or a list of them), as in the pickle.
- Topic filter defaults to `#`; set `MQTT_TOPIC`, `MQTT_HOST`, `MQTT_PORT`, `MQTT_CA_CERT`, `MQTT_CLIENT_CERT`, `MQTT_CLIENT_KEY` in `.env`.
- "Stale" = no new reading for `STALE_AFTER_SECONDS` (default 60).
