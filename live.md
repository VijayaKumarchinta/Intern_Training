# Live Dashboard Review and Design

## Project Review: live_dashboard

### Existing Architecture (Already Built)

The `live_dashboard` folder contains a complete IIoT live-stream dashboard system that was designed in 8 phases. Key components already in place:

**Data Flow Already Designed:**

```
Excel Dataset → JSONL → MQTT Simulator → Mosquitto Broker → Consumer (validation + DB) → PostgreSQL → Flask REST + Socket.IO → Vue 3 Dashboard (WebSocket)
```

**Database Schema (4 tables, normalized):**

1. `sensor_definitions` — 31 sensor tags, machine/area/unit inlined
2. `telemetry_samples` — one row per MQTT message (idempotent on `message_id`)
3. `sensor_readings` — one row per sensor per message (31 readings per sample)
4. `system_events` — optional append-only operational log

**MQTT Contract (Frozen):**

- Topic: `factory/line_speed_30/telemetry` (simulator → consumer, QoS 1)
- Topic: `factory/line_speed_30/notify` (consumer → Flask, QoS 0, after COMMIT)
- Payload: 31 sensor tags + `schema_version`, `machine_code`, `session_label`, `message_id`, `sequence_number`, `event_timestamp`, `source_millitm`, `delta_t`, `source`
- Notify payload: `{message_id, sample_id, event_timestamp}` — published only after DB commit

**Dataset Already Processed:**

- `line30_replay.jsonl` — 2,139 records × 35 columns, zero missing values
- 31 sensor tags mapped from Excel columns (see sensor-mapping.md)
- Known anomalies documented (duplicate signals, inactive channels, etc.)

**Frontend Skeleton:**

- Vue 3 + Vite + Apache ECharts
- Structure: `src/components`, `src/views`, `src/composables` (useSocket, useTelemetry, useHistory)
- ECharts for real-time charts, KPI cards for key metrics

**Earlier Phases Partially Implemented:**

- Backend routes: overview, latest, history, trends, events, status, replay-control
- Backend services: queries, notify_listener
- Backend sockets: dashboard.py (Socket.IO namespace `/dashboard`)
- Empty Python files awaiting implementation

### What Already Works Well

✅ MQTT pub/sub architecture with QoS 1 idempotency  
✅ PostgreSQL normalized schema (3 core tables + optional events)  
✅ Sensor mapping with 31 fixed tags (frozen, not changing)  
✅ Dataset already imported and validated (2,139 samples, 66,309 readings)  
✅ Architecture documented across 8 phases with exit criteria  
✅ WebSocket push architecture (not polling)  
✅ Commit-before-broadcast pattern (Flask-SocketIO reads from DB after consumer commit)  

### Gaps and What Needs Building

❌ Backend services are partially implemented (empty/placeholder files)  
❌ Socket.IO notify listener not fully wired  
❌ Flask routes need full implementation  
❌ Vue composables need Socket.IO integration  
❌ ECharts configs for real-time streaming  
❌ 5-second refresh requirement (currently design is event-driven, which is better)  
❌ End-to-end test suite  

---

## Design Plan: Live Streaming Dashboard

### Core Requirements (From User Request)

1. **Pub/sub via MQTT** (not direct from Excel) — data comes through MQTT broker
2. **Data stored in PostgreSQL** after validation through broker
3. **WebSockets** for live stream between frontend and backend
4. **Dashboard refreshes every 5 seconds** — data injected through broker, stored in DB, reflects on frontend
5. **Dashboard must reflect live data** from the broker/db pipeline

### Architecture (Updated for Requirements)

```text
┌─────────────────────────────────────────────────────────────────┐
│                       LIVE STREAMING PIPELINE                  │
├─────────────┬───────────────────────┬───────────────────────┤
│  Simulator  │         MQTT          │   PostgreSQL          │
│ (source)    │  (factory/... topics) │  (4 normalized tables)│
│             │                       │                       │
│  → publishes│                       │                       │
│  JSON payloads│                    │                       │
│  (31 sensors)|                       │                       │
└─────┬───────└───────────────────────┘                       │
      │                                                         │
      ▼                                                         ▼
┌───────────────────────┐              ┌───────────────────────┐
│   Mosquitto Broker    │              │   consumer service    │
│   (factory/...       │              │   (validate + insert) │
│    topics, QoS 1)    │              └─────┬────────────────┘
      │                                   ▲  After COMMIT:     │
      │                                   │  publish notify     │
      │                                   │  payload to notify  │
      ▼                                   │  topic              │
┌───────────────────────┐              └─────┬────────────────┘
│   Flask Backend       │                  ▼               │
│   (REST + Socket.IO) │           ┌─────────────────┐ │
│   • subscribes to    │           │   Flask-SocketIO│ │
│     factory/.../notify│          │   (emits to     │ │
│   • reads assembled  │           │   browser clients)││
│     payload from DB  │           └─────────────────┘ │
│   • emits            │                │                   │
│     telemetry_update│                ▼                   │
└────────────┬─────────┘              ┌─────────────────┘ │
             │                        │  WebSocket       │
             │                        │  /dashboard      │
             ▼                        │  namespace       │
┌───────────────────────┐              └───────┬─────────────┘
│   Vue 3 Dashboard     │              5-second    │
│   (frontend)          │              refresh cycle   │
│   • hydrates from    │              (GET /api/line/30/overview)│
│     REST API         │              every 5s           │
│   • receives         │              • on refresh: data injected│
│     via WebSocket    │              through broker → DB → WS │
│     telemetry_update │                           │
└───────────────────────┘
```

### Data Flow (Per the User's Requirements)

1. **Simulator** (or real PLC/edge gateway) publishes JSON payloads to `factory/line_speed_30/telemetry` topic on MQTT broker
   - Payload includes 31 sensor values + metadata (`message_id`, `sequence_number`, `event_timestamp`, `source`)
   - QoS 1 for at-least-once delivery with idempotency via `message_id`

2. **Mosquitto Broker** receives and routes the messages

3. **Consumer service** (Python, Paho client):
   - Subscribes to `factory/line_speed_30/telemetry`
   - Validates payload against JSON Schema (31 tags present, types correct)
   - Resolves each sensor tag → `sensor_id` from `sensor_definitions` table
   - **One transaction**: inserts `telemetry_samples` header + all 31 `sensor_readings` rows
   - On duplicate `message_id`: log and skip (idempotent, no crash)
   - **After COMMIT**: publishes compact notify payload to `factory/line_speed_30/notify`

4. **Flask Backend** (Flask-SocketIO):
   - Subscribes to `factory/line_speed_30/notify` on background thread
   - On notify receipt: reads assembled payload from database (sample_id + all sensor readings)
   - Emits `telemetry_update` event to all connected browser clients via WebSocket (`/dashboard` namespace)
   - Also provides REST endpoints for dashboard hydration

5. **Vue 3 Dashboard**:
   - **On mount**: `GET /api/line/30/overview` to hydrate initial KPIs and latest values from REST
   - **Open WebSocket**: connect to `/dashboard` namespace
   - **On `telemetry_update` event**:
     - Update KPI cards with new sensor values
     - Append to ECharts bounded history buffer
     - Update last-seen timestamp
   - **Every 5 seconds** (user requirement):
     - `GET /api/line/30/overview` refreshes KPI cards
     - Ensures data is current even if WebSocket misses some events
     - Fills any gaps from the REST API
   - **Disconnect handling**: show degraded banner, auto-reconnect with exponential backoff

### Database Design (Confirming the 4-table schema)

```sql
-- 1. sensor_definitions (31 sensors, frozen)
CREATE TABLE line30.sensor_definitions (
    sensor_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    machine_code VARCHAR(50) NOT NULL DEFAULT 'LINE_30' CHECK (machine_code = 'LINE_30'),
    area_name VARCHAR(50) NOT NULL CHECK (area_name IN ('Burner','Thermal','Oil System','Pump','Moisture Control','Speed Control','Valve')),
    unit_code VARCHAR(30),  -- NULL until engineering confirms
    sensor_tag VARCHAR(100) NOT NULL,
    source_column VARCHAR(200) NOT NULL,
    sensor_name VARCHAR(150) NOT NULL,
    data_type VARCHAR(15) NOT NULL DEFAULT 'NUMERIC' CHECK (data_type IN ('NUMERIC','BOOLEAN')),
    signal_role VARCHAR(20) NOT NULL CHECK (signal_role IN ('PV','SP','CV','MEASUREMENT','STATUS','UNKNOWN')),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (machine_code, sensor_tag),
    UNIQUE (machine_code, source_column)
);

-- 2. telemetry_samples (one row per MQTT message)
CREATE TABLE line30.telemetry_samples (
    sample_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    machine_code VARCHAR(50) NOT NULL DEFAULT 'LINE_30' CHECK (machine_code = 'LINE_30'),
    message_id UUID NOT NULL UNIQUE,          -- idempotency key
    sequence_number BIGINT NOT NULL,           -- ordering / debug only
    session_label VARCHAR(50),                 -- optional replay tag
    event_timestamp TIMESTAMPTZ NOT NULL,      -- measurement time
    source_millitm BIGINT,                     -- preserved from dataset
    delta_t DOUBLE PRECISION,                  -- preserved from dataset
    source VARCHAR(30) NOT NULL,               -- DATASET_REPLAY / PLC / EDGE
    schema_version VARCHAR(20) NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. sensor_readings (31 readings per sample)
CREATE TABLE line30.sensor_readings (
    reading_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sample_id BIGINT NOT NULL REFERENCES line30.telemetry_samples(sample_id) ON DELETE CASCADE,
    sensor_id BIGINT NOT NULL REFERENCES line30.sensor_definitions(sensor_id),
    numeric_value DOUBLE PRECISION NOT NULL,
    UNIQUE (sample_id, sensor_id)
);

-- Indexes for time-series queries
CREATE INDEX idx_samples_machine_time ON line30.telemetry_samples(machine_code, event_timestamp DESC);
CREATE INDEX idx_readings_sensor_sample ON line30.sensor_readings(sensor_id, sample_id);
```

### 5-Second Refresh Implementation

The user specifically requested "dashboard have to refresh every 5 seconds and that time the data has to inject though broker and stored in db and reflecting the frontend dashboard."

**Implementation approach:**

```javascript
// In Vue composable useTelemetry.js
const refreshInterval = 5000; // 5 seconds

// Initial fetch on mount
onMounted(() => {
  fetchOverview();
  // Start interval
  refreshId = setInterval(fetchOverview, refreshInterval);
});

// On component unmount
onUnmounted(() => {
  if (refreshId) clearInterval(refreshId);
});

// Refresh function
async function fetchOverview() {
  try {
    const response = await axios.get('/api/line/30/overview');
    // Update KPI cards from response data
    updateKPIs(response.data);
    // Also push to WebSocket if connected
    if (socketConnected) {
      socket.emit('refresh-request');  // Optional: notify backend
    }
  } catch (error) {
    console.error('Failed to refresh dashboard data:', error);
  }
}
```

**Why 5-second REST refresh + WebSocket push?**

- WebSocket provides real-time updates when new data arrives (instant)
- 5-second REST ensures data is current even if WebSocket missed events or client disconnected
- Combined: live feel from WS + guaranteed consistency from 5s REST poll
- The REST call itself goes through the same pipeline: broker → consumer → DB → Flask → REST endpoint

**What the 5-second refresh does:**

1. `GET /api/line/30/overview` → Flask queries DB → returns KPIs (paddle speed, moisture PV, oil temp, pump loading, etc.)
2. Dashboard KPI cards update with latest values from DB
3. If WebSocket has newer data, it overrides the REST data (WS takes priority)
4. ECharts charts append new points from either source

### MQTT Topic Design (Updated)

| Topic | Direction | QoS | Purpose |
| ------- | ----------- | ----- | --------- |
| `factory/line_speed_30/telemetry` | simulator → consumer | 1 | Main telemetry data (31 sensors) |
| `factory/line_speed_30/notify` | consumer → Flask | 0 | Post-commit notification |
| `factory/line_speed_30/status` | simulator → * | 1 | Broker/connection status |
| `factory/line_speed_30/control` | backend → simulator | 1 | Start/pause/resume/stop (optional) |

### Requirements Checklist

- [x] Pub/sub via MQTT (not direct from Excel) — data flows through broker
- [x] Data stored in PostgreSQL after validation through broker
- [x] WebSockets for live stream between frontend and backend
- [x] Dashboard refreshes every 5 seconds (REST + WS hybrid)
- [x] Data injected through broker → stored in DB → reflects on frontend
- [x] Dashboard reflects live data (KPIs update, charts animate)
- [x] 5-second refresh cycle ensures data consistency

### Files to Create/Modify in live_dashboard

**Create (new implementation):**

1. `live_dashboard/backend/services/telemetry_processor.py` — tag→sensor_id resolution, transaction builder
2. `live_dashboard/backend/sockets/notify_listener.py` — subscribe to notify topic, trigger Flask emit
3. `live_dashboard/backend/routes/telemetry.py` — REST endpoints for overview/latest/history
4. `live_dashboard/frontend/src/composables/useTelemetry.js` — Socket.IO + 5s refresh logic
5. `live_dashboard/frontend/src/components/KPICards.vue` — display paddle_speed, moisture_pv, oil_temp, pump_loading
6. `live_dashboard/frontend/src/components/Charts.vue` — ECharts with bounded history
7. `live_dashboard/consumer/telemetry_processor.py` — validated transaction builder (enhance existing)
8. `live_dashboard/docs/websocket-contract.md` — Socket.IO event contract

**Modify (enhance existing):**

1. `live_dashboard/backend/app.py` — wire Socket.IO, SQLAlchemy, routes
2. `live_dashboard/backend/extensions.py` — SQLAlchemy + SocketIO extensions
3. `live_dashboard/consumer/subscriber.py` — enhance validation + idempotent insert
4. `live_dashboard/simulator/payload_builder.py` — ensure 31-tag payload with message_id

**Can remove/clean (already have data, just need wiring):**

- Empty Python files that are placeholders
- Empty Vue files that need proper implementation
- Empty requirements.txt that need actual dependencies

### Key Design Decisions

1. **Commit-before-broadcast**: Consumer always commits DB transaction first, THEN publishes notify. Flask only emits after reading assembled payload from DB. Browser never sees partial writes.

2. **5-second REST refresh is intentional**: Not a compromise — it guarantees consistency across restarts, reconnections, and provides fallback when WS missed events. The WS provides "instant" feel; REST provides "guaranteed current."

3. **MQTT is the seam**: Swapping simulator for real PLC just changes `source` field in payload, no downstream changes needed.

4. **31 sensors fixed**: The sensor_definitions table is frozen — adding sensors requires a migration, not ad-hoc changes.

5. **Units = NULL, KPI cards show "TBD"**: Per the existing design, engineering confirms units later. Dashboard doesn't assume °C, bar, etc.

### Exit Criteria for This Implementation

- [ ] Simulator publishes 31-sensor payloads to MQTT broker
- [ ] Consumer validates, inserts atomic sample+31 readings into PostgreSQL
- [ ] On duplicate message_id: exactly one insert, no crash
- [ ] After COMMIT, consumer publishes notify payload
- [ ] Flask-SocketIO receives notify, reads from DB, emits telemetry_update
- [ ] Vue dashboard receives telemetry_update, updates KPIs and charts
- [ ] 5-second REST refresh cycle works (GET /api/line/30/overview returns current data)
- [ ] Dashboard refreshes every 5s and values change (live feel)
- [ ] WebSocket disconnect: dashboard shows degraded banner, auto-reconnects
- [ ] Full cycle verified: simulator → MQTT → consumer → DB → Flask → WS → dashboard
- [ ] All exit criteria met → milestone complete

---
*Design based on live_dashboard project learnings (Aug–Oct 2026 training period at Triniti Advanced Software Labs). MQTT pub/sub architecture, PostgreSQL normalized schema, Flask-SocketIO WebSocket push, Vue 3 event-driven dashboard. 5-second REST refresh ensures consistency alongside real-time WS push.*
