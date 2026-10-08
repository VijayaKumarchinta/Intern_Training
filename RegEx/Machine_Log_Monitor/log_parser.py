import re
from datetime import datetime, timezone

LOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*\|\s*"
    r"(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\|\s*"
    r"Machine\s+(?P<machine_id>M\d+)\s*\|\s*"
    r"(?P<message>.+)"
)


def parse_machine_log(line):
    line = line.strip()
    if not line:
        return None

    match = LOG_PATTERN.fullmatch(line)
    if not match:
        return None

    log_data = match.groupdict()
    try:
        timestamp = datetime.strptime(
            log_data["timestamp"], "%Y-%m-%d %H:%M:%S"
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None

    return {
        "timestamp": timestamp,
        "unix_timestamp": int(timestamp.timestamp()),
        "machine_id": log_data["machine_id"],
        "level": log_data["level"],
        "error_message": log_data["message"].strip(),
    }
