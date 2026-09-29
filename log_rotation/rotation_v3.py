"""v3 — v2 plus cross-run retention cleanup (production-ish).

Everything from v2 (hybrid time + size, timestamped per-run base file),
plus the one thing v2 lacks: finished runs' log files accumulate in
logs/ forever, because backupCount only prunes *within* one run's
sequence-numbered chain.

Fix: after configuring logging, sweep the logs directory once at startup
and delete app_*.log* files (and their rotated chains) whose run started
longer than RETENTION_DAYS ago — parsed from the filename's timestamp,
not from mtime, so reorganizing files doesn't reset their clock.
"""

from datetime import datetime, timedelta
import glob
import logging
import os
import time

from logging.handlers import RotatingFileHandler


class TimeAndSizeRotatingHandler(RotatingFileHandler):
    def __init__(
        self,
        filename,
        max_bytes,
        count,
        interval=1,
        encoding="utf-8",
    ):
        self.interval = interval
        self.next_rollover_time = time.time() + interval

        super().__init__(
            filename=filename,
            maxBytes=max_bytes,
            backupCount=count,
            encoding=encoding,
        )

    def shouldRollover(self, record):
        if time.time() >= self.next_rollover_time:
            return 1
        if self.maxBytes <= 0:
            return 0

        if self.stream is None:
            self.stream = self._open()

        self.stream.seek(0, os.SEEK_END)
        current_size = self.stream.tell()

        message = self.format(record)
        message_size = len(
            (message + self.terminator).encode(
                self.encoding or "utf-8"
            )
        )

        return current_size + message_size >= self.maxBytes

    def doRollover(self):
        super().doRollover()
        self.next_rollover_time = time.time() + self.interval


def cleanup_old_runs(logs_dir, retention_days):
    """Delete app_*.log* files from runs older than retention_days.

    Age comes from the YYYY-MM-DD_HH-MM-SS embedded in the filename, so
    the sweep is stable regardless of file mtimes. Both the live file
    (app_<ts>.log) and its rotated chain (app_<ts>.log.N) are removed.
    """
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed = 0

    for path in glob.glob(os.path.join(logs_dir, "app_*.log*")):
        name = os.path.basename(path)
        # app_2026-09-29_15-59-21.log            -> ts part
        # app_2026-09-29_15-59-21.log.3          -> same ts part
        stem = name[len("app_"):].split(".log")[0]
        try:
            run_started = datetime.strptime(
                stem, "%Y-%m-%d_%H-%M-%S"
            )
        except ValueError:
            continue  # not one of ours — leave it alone

        if run_started < cutoff:
            os.remove(path)
            removed += 1

    return removed


RETENTION_DAYS = 7

log_file = (
    f"logs/app_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
)

os.makedirs("logs", exist_ok=True)

removed = cleanup_old_runs("logs", RETENTION_DAYS)

handler = TimeAndSizeRotatingHandler(
    filename=log_file,
    max_bytes=1024,
    count=10,
    interval=10,
    encoding="utf-8",
)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

handler.setFormatter(formatter)

logger = logging.getLogger("application")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

logger.info(f"Retention sweep removed {removed} old run file(s)")
logger.info("Application started")
logger.info("Processing request")
logger.warning("Something requires attention")

for i in range(100):
    logger.info(f"Testing log rotation - message number {i}")
