# Architecture Documentation

Line Speed 30 IIoT Platform architecture overview following the seven-week implementation sequence and 15 architecture rules.

## Core Stack

- **Frontend:** Vue 3, Pinia, ECharts 5
- **Backend:** Python, Flask, SQLAlchemy
- **Database:** PostgreSQL
- **Messaging:** Eclipse Mosquitto, Paho MQTT
- **Realtime:** WebSockets

## Seven-Week Sequence

Week 1: Database foundation | Week 2: HTTP API | Week 3: MQTT ingestion | Week 4: WebSocket foundation | Week 5: Frontend dashboard | Week 6: Bidirectional ops | Week 7: Production hardening

## 15 Architecture Rules

1. MQTT is the ingestion boundary
2. PostgreSQL is the source of truth
3. Excel is dev/testing fixture only
4. Every message processed individually
5. Persist before broadcasting
6. No frontend telemetry polling
7. No SQL in route handlers
8. No DB access in WebSocket hub
9. No Flask deps in services
10. No duplicate signal-limit config
11. No hardcoded KPI values
12. No duplicate MQTT subscribers
13. No independent replay state in browser components
14. No in-memory-only WS registry at scale
15. No Redis/Kafka until justified
