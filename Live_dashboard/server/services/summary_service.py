
from datetime import datetime, timedelta

from server.repositories.summary_repository import get_hourly_summary_data


def _number(value):
    return float(value) if value is not None else None


def get_hourly_summary(
    line_id: str,
    hours: int | None = None,
    cycle_id: str | None = None,
    hour_start: datetime | None = None,
) -> dict:
    result = get_hourly_summary_data(line_id, hours, cycle_id, hour_start)

    if result is None:
        return {
            "cycle_id": None,
            "window_start": None,
            "window_end": None,
            "hours": hours,
            "sample_count": 0,
            "data": [],
            "statistics": {},
        }

    cycle_id = result["cycle_id"]
    window_start = result["window_start"]
    window_end = result["window_end"]
    stats = result["statistics"]
    prefixes = {
        "oil_temperature": "burner_pv",
        "delta_t": "delta_t",
        "burner_load": "burner_load",
        "moisture": "moisture",
        "paddle_speed": "paddle_speed",
        "oil_level": "oil_level",
    }
    statistics = {
        key: {
            "average": _number(stats[f"{prefix}_avg"]),
            "minimum": _number(stats[f"{prefix}_min"]),
            "maximum": _number(stats[f"{prefix}_max"]),
        }
        for key, prefix in prefixes.items()
    }
    data = []
    for row in result["hourly_rows"]:
        item = {
            "hour_start": row["hour_start"].isoformat(),
            "sample_count": row["sample_count"],
            "burner_at_100_seconds": float(row["burner_at_100_seconds"]),
        }
        for prefix in prefixes.values():
            item[f"{prefix}_average"] = _number(row[f"{prefix}_avg"])
            item[f"{prefix}_minimum"] = _number(row[f"{prefix}_min"])
            item[f"{prefix}_maximum"] = _number(row[f"{prefix}_max"])
        data.append(item)

    return {
        "cycle_id": str(cycle_id),
        "window_start": window_start.isoformat(),
        "window_end": (window_end + timedelta(hours=1)).isoformat(),
        "hours": len(data),
        "sample_count": stats["sample_count"],
        "data": data,
        "statistics": statistics,
    }
