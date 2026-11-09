# Decisions Documentation

## Key Design Decisions

### MQTT as Ingestion Boundary

- MQTT is the sole entry point for industrial telemetry
- No alternative protocols at the boundary
- Subscriber processes messages one at a time in transaction

### PostgreSQL as Source of Truth

- All persisted data lives in PostgreSQL
- No Redis cache for critical state until Week 7 justified
- telemetry_latest is operational projection, not replacement for historical facts

### Persist Before Broadcast

- Database commit must succeed before WebSocket broadcast
- Failed transactions produce no telemetry update
- Ensures data consistency between DB and frontend

### Seven-Week Sequence

- Mandatory order: DB → API → MQTT → WS → Frontend → Ops → Hardening
- Each week builds on previous foundation
- Cannot skip or reorder without violating architecture rules

### Flat Deployment Model (Initial)

- Single application process for initial deployment
- In-memory WebSocket client registry
- Gevent-compatible WebSocket server
- Redis/Pub/Sub added only if multi-process becomes required

### No Frontend Polling

- Live updates via WebSocket only
- Historical window changes trigger new HTTP requests
- CSV export is explicit user-driven HTTP operation

### Repository Pattern

- Business rules kept out of route handlers
- Services depend on repository interfaces, not Flask
- Enables testing and alternative implementations

### Vue 3 + Pinia + ECharts 5

- Modern frontend stack per architecture requirements
- Pinia for shared state across components/composables
- ECharts 5 for all five chart visualizations
