# WebSocket Documentation

Endpoint: WS /ws/v1

## Server → Client Frames

- `latest` - New committed telemetry with values object
- `alarm.raised` - New alarm occurrence
- `alarm.cleared` - Alarm returned to normal
- `alarm.acked` - Alarm acknowledgement
- `event.created` - New event history item
- `replay.state` - Shared replay state synchronization
- `ack` - Command acknowledgement
- `error` - Command/protocol failure
- `session.expired` - Authentication/session expiration

## Client → Server Commands

- `replay.start` - Start or resume replay
- `replay.pause` - Pause replay
- `replay.speed` - Change replay speed
- `replay.reset` - Reset replay position
- `alarm.ack` - Acknowledge an alarm

## Frame Example

Telemetry: `{type: "latest", machine_code, ts, seq, values: {...}, status}`
Command: `{type: "replay.speed", command_id, speed}`
