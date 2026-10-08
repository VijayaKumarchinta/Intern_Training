import logging
from log_reader import MachineLogReader
from log_parser import parse_machine_log
from machine_insert import store_errors
from report import generate_report

logger = logging.getLogger(__name__)

reader = MachineLogReader()


def monitor_machine_logs():
    result = reader.read_next_line()
    if result is None:
        reader.close()
        return False

    line_number, line, is_last_line = result

    try:
        parsed = parse_machine_log(line)
        if parsed is None:
            if line.strip():
                logger.warning(
                    "Skipping line %d: invalid log format or timestamp",
                    line_number,
                )
            else:
                logger.info("Skipping line %d: blank line", line_number)
        elif parsed["level"] == "ERROR":
            store_errors([parsed])
            generate_report()
        else:
            logger.info(
                "Skipping line %d: level is %s; only ERROR is stored",
                line_number,
                parsed["level"],
            )
    except Exception:
        reader.retry_last_line()
        raise

    if is_last_line:
        reader.close()
        return False

    return True
