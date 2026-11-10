# MQTT Topic Contract — Phase 2a

Frozen 2026-11-10. Broker: Mosquitto 2.1.2, foreground on `127.0.0.1:1883`.

## Runtime model

The Windows `mosquitto` service is installed and running, but it does not
read this project's configuration — its service definition is
`mosquitto.exe run` without `-c`, so it uses stock defaults and is not
bound to 1883. The service is not stopped (stopping requires elevation)
but it does not interfere with the foreground broker.

Phase 2 runs the broker manually in the foreground:
& "C:\Program Files\Mosquitto\mosquitto.exe" -c "C:\Program Files\Mosquitto\mosquitto.conf" -v
## Persistence

Database: `C:\ProgramData\mosquitto\data\mosquitto.db`
Configured via `persistence true` and `persistence_location` in
`mosquitto.conf`. Retained messages survive broker restarts.

## Topic hierarchy
line30/telemetry/{machine_code}
line30/state/{machine_code}
line30/command/{machine_code}

## Direction, QoS, retention

| Topic | Direction | QoS | Retain | Purpose |
|---|---|---:|---|---|
| `line30/telemetry/LINE_30` | publisher -> broker -> ingestion | 1 | false | One JSON `TelemetryRecord` per message |
| `line30/state/LINE_30` | publisher -> broker | 1 | true | Publisher liveness (`online` / `offline`) |
| `line30/command/LINE_30` | operator -> publisher | 1 | false | Reserved for Phase 4 (start/stop/pause) |

## Payload shapes

### Telemetry

Exact schema in `backend/contract/schema.py`. One message per record.
The `machine_code` field in the payload MUST match the `{machine_code}`
segment of the topic. Ingestion rejects any mismatch.

### State

```json
{"machine_code":"LINE_30","status":"online"}
Valid status values: online, offline.

Last-Will
The publisher connects with a retained Last-Will on
line30/state/LINE_30 with payload
{"machine_code":"LINE_30","status":"offline"}.

On clean connect: publishes retained {"machine_code":"LINE_30","status":"online"}.
On clean disconnect: publishes retained {"machine_code":"LINE_30","status":"offline"}.

Subscribers receive the current state immediately on connect without
polling, because the state topic is retained.

Machine code
LINE_30. Constant in backend/contract/schema.py. Multiple machines
each get their own line30/telemetry/{machine_code} topic and their own
MACHINE_CODE constant. The topic root line30/ is a project namespace,
not a per-machine prefix.

Verification log
2026-11-10 12:25:30 — Broker started foreground from mosquitto.conf; bound 1883.
2026-11-10 12:26:31 — Autosave succeeded (no error).
2026-11-10 12:26:59 — mosquitto_pub -r state message accepted with r1; PUBACK received.
2026-11-10 12:27:00 — mosquitto_pub telemetry message accepted with r0; PUBACK received.
2026-11-10 12:27:07 — First mosquitto_sub on line30/# received retained state, no telemetry.
2026-11-10 12:27:22 — Second mosquitto_sub (after disconnect) received retained state again.
2026-11-10 12:27:32 — Autosave succeeded again (no error).

## Phase 2b verification

2026-11-10 12:39:46 — Broker restarted, restored 1 retained message (previous session's state).
2026-11-10 12:40:13 — `MqttClient` connected as `live_dashboard-LINE_30-21c00cfe`.
2026-11-10 12:40:13 — Last-Will registered: `line30/state/LINE_30` (r1, q1, 45 bytes).
2026-11-10 12:40:13 — Retained `online` published to state topic (m1, r1, q1).
2026-11-10 12:40:14 — Telemetry published to telemetry topic (m2, r0, q1).
2026-11-10 12:40:14 — Retained `offline` published to state topic (m3, r1, q1).
2026-11-10 12:40:14 — Clean DISCONNECT.

## Phase 2c verification

2026-11-10 12:53:08 — First `python -m publisher --limit 5 --interval 0.5` run.
2026-11-10 12:53:11 — Clean shutdown, 5 records published.
2026-11-10 12:53:40 — Second run with active subscriber.
2026-11-10 12:53:40 — `live_dashboard-LINE_30-publisher` connected; Last-Will registered.
2026-11-10 12:53:40 — Retained `online` published.
2026-11-10 12:53:40..42 — 5 telemetry records delivered to subscriber `auto-55C6C947...`.
2026-11-10 12:53:42 — Retained `offline` published; clean DISCONNECT.
2026-11-10 12:53:42 — Subscriber printed 5 strictly increasing event_timestamps:
  2026-04-17T12:09:53.162
  2026-04-17T12:10:03.163
  2026-04-17T12:10:13.164
  2026-04-17T12:10:23.165
  2026-04-17T12:10:33.166

## Phase 2d verification

OK: received=5 accepted=5 rejected=0
First 5 accepted event timestamps:
  2026-04-17T12:09:53.162
  2026-04-17T12:10:03.163
  2026-04-17T12:10:13.164
  2026-04-17T12:10:23.165
  2026-04-17T12:10:33.16

## State topic ownership

Only the **publisher** publishes to `line30/state/LINE_30`. Ingestion and
API components subscribe only. This avoids the state topic flickering to
`offline` when a non-publisher component shuts down cleanly while the
publisher is still running.

Phase 4 action: add `state_publish: bool = True` to `MqttClient.__init__`
and set it to `False` for ingestion and API roles.

