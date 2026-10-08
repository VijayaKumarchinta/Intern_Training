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

    parsed = parse_machine_log(line)
    if parsed is None:
        logger.warning("Skipping invalid line %d", line_number)

    else:
        if parsed["level"] == "ERROR":
            store_errors([parsed])

    generate_report()

    if is_last_line:
        reader.close()
        return False

    return True