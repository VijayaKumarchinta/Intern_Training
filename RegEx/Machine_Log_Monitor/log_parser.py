import logging
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

LOG_PATTERN = re.compile(
    r"(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s*\|\s*"
    r"(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\|\s*"
    r"Machine\s+(?P<machine_id>M\d+)\s*\|\s*"
    r"(?P<message>.+)"
)

def parse_machine_log(lines):
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = LOG_PATTERN.fullmatch(line)
        if not match:
            logger.warning("Invalid log format: %s",line)
            continue

        log_data = match.groupdict()
        if log_data["level"] != "ERROR":
            continue

        normal_timestamp = datetime.strptime(log_data["timestamp"],"%Y-%m-%d %H:%M:%S")
        normal_timestamp = normal_timestamp.replace(tzinfo=timezone.utc)

        unix_timestamp = int(normal_timestamp.timestamp())

        error_data = {
            "timestamp": normal_timestamp,
            "unix_timestamp": unix_timestamp,
            "machine_id": log_data["machine_id"],
            "error_message": log_data["message"].strip()
        }
    logger.info("ERROR detected: machine=%s timestamp=%s",error_data["machine_id"],error_data["timestamp"])
    return None
