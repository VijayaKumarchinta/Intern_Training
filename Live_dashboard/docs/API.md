# API Documentation

All endpoints under `/api/v1`. Six endpoints with GET methods.

## Endpoints

### GET /health

- Purpose: Operational health check
- Response: `{status, database, broker, subscriber, last_message_age_s}`
- Must represent actual dependency states

### GET /history

- Purpose: Historical telemetry queries
- Params: window (15m/30m/45m/full), limit (max 5000), machine_code
- Backend validates parameters and imposes record limits

### GET /stats

- Purpose: Aggregated signal statistics
- Returns: min, max, average, sample count, out-of-limit info per signal
- Uses appropriate numeric precision, avoids integer division

### GET /manifest

- Purpose: Dataset metadata and replay information
- Reading count, source timestamp range, dataset metadata

### GET /alarms

- Purpose: Active and historical alarm occurrences
- Params: active=true, machine_code, severity

### GET /export

- Purpose: CSV download of historical readings
