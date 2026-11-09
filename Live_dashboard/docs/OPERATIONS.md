# Operations Documentation

## Seven-Week Completion Criteria

### Week 1 - Database Foundation

- Telemetry can be persisted using normalized database design
- Repositories use ON CONFLICT DO NOTHING for duplicate protection
- SQLAlchemy models for all 10 tables operational

### Week 2 - HTTP API

- /health endpoint with actual dependency states
- /history with window and limit parameters
- /stats with min/max/average/sample count
- /manifest with dataset metadata
- /alarms with active filtering
- /export for CSV download

### Week 3 - MQTT Ingestion

- Mosquitto broker integration
- Paho subscriber processing sequence
- Validation → Resolution → Transaction → Commit → Broadcast
- Invalid messages logged and rejected without terminating subscriber

### Week 4 - WebSocket Foundation

- WS /ws/v1 connection with authentication
- Committed telemetry broadcast after DB commit
- Replay state synchronization
- Command acknowledgements with correlation IDs

### Week 5 - Frontend Dashboard

- Vue layout reproduces HTML dashboard
- KPI cards with animated values and sparklines
- Five chart views with ECharts 5
- HTML visual parity (light grey bg, navy header, blue accent)

### Week 6 - Bidirectional Operations

- Pause/resume, speed controls, alarm acknowledgement
- Command synchronization across clients
- Replay state management with in-process control

### Week 7 - Production Hardening

- Structured JSON logging with UTC timestamps
- Correlation/message identifiers
- Reconcile reconnects, invalid payloads, database failures
- Testing unit and integration tests
- Deployment with Waitress/Gevent
