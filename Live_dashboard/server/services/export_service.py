
import csv
import io
import json

from server.repositories.export_repository import get_readings_for_export
from server.services.event_service import get_event_history
from server.services.summary_service import get_hourly_summary


def _build_csv(headers, rows):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    return output.getvalue()


def build_hourly_summary_csv(line_id: str, hours: int | None = None, cycle_id=None, hour_start=None):
    summary = get_hourly_summary(line_id, hours, cycle_id, hour_start)

    headers = [
        "Hour Start", "Sample Count",
        "Burner PV Average", "Burner PV Minimum", "Burner PV Maximum",
        "Delta T Average", "Delta T Minimum", "Delta T Maximum",
        "Burner Load Average", "Burner Load Minimum", "Burner Load Maximum",
        "Moisture Average", "Moisture Minimum", "Moisture Maximum",
        "Paddle Speed Average", "Paddle Speed Minimum", "Paddle Speed Maximum",
        "Oil Level Average", "Oil Level Minimum", "Oil Level Maximum",
        "Burner at 100% Seconds",
    ]

    rows = [
        [
            item["hour_start"],
            item["sample_count"],
            item["burner_pv_average"],
            item["burner_pv_minimum"],
            item["burner_pv_maximum"],
            item["delta_t_average"],
            item["delta_t_minimum"],
            item["delta_t_maximum"],
            item["burner_load_average"],
            item["burner_load_minimum"],
            item["burner_load_maximum"],
            item["moisture_average"],
            item["moisture_minimum"],
            item["moisture_maximum"],
            item["paddle_speed_average"],
            item["paddle_speed_minimum"],
            item["paddle_speed_maximum"],
            item["oil_level_average"],
            item["oil_level_minimum"],
            item["oil_level_maximum"],
            item["burner_at_100_seconds"],
        ]
        for item in summary["data"]
    ]

    return _build_csv(headers, rows)


def build_readings_csv(line_id: str, limit: int = 50000, cycle_id=None, start=None, end=None):
    rows = get_readings_for_export(line_id, limit, cycle_id, start, end)

    headers = [
        "ID", "Message ID", "Replay Session ID", "Replay Cycle ID",
        "Replay Cycle Number", "Line ID", "Event Timestamp",
        "Received At", "Payload",
    ]

    data = [
        [
            row["id"],
            row["message_id"],
            row["replay_session_id"],
            row["replay_cycle_id"],
            row["replay_cycle_number"],
            row["line_id"],
            row["event_ts"].isoformat(),
            row["received_at"].isoformat(),
            json.dumps(row["payload"], ensure_ascii=False),
        ]
        for row in rows
    ]

    return _build_csv(headers, data)


def build_events_csv(line_id: str, limit: int = 50000, cycle_id=None, start=None, end=None):
    events = get_event_history(line_id, limit, cycle_id, start, end)

    headers = [
        "ID", "Line ID", "Event Type", "Event Code", "Severity",
        "State", "Title", "Description", "Event Timestamp",
        "Recorded At", "Reading ID", "Replay Cycle ID", "Details",
    ]

    rows = [
        [
            event["id"],
            event["line_id"],
            event["event_type"],
            event["event_code"],
            event["severity"],
            event["state"],
            event["title"],
            event["description"],
            event["event_ts"],
            event["recorded_at"],
            event["reading_id"],
            event["replay_cycle_id"],
            json.dumps(event["details"], ensure_ascii=False),
        ]
        for event in events
    ]

    return _build_csv(headers, rows)
