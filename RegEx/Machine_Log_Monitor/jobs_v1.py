import logging

from log_reader import read_machine_logs
from log_parser import parse_machine_log
from machine_insert import store_errors
from report import generate_report

logger = logging.getLogger(__name__)


def monitor_machine_logs():
    logger.info("Monitoring started")

    lines = read_machine_logs()

    errors = parse_machine_log(lines)

    store_errors(errors)

    generate_report()

    logger.info("Monitoring completed")