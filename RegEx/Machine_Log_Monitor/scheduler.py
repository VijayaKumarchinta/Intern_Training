import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from jobs import monitor_machine_logs
from logging_config import configure_logging

logger = logging.getLogger(__name__)

def create_scheduler():

    scheduler = BlockingScheduler()

    def run_monitoring():
        has_more_lines = monitor_machine_logs()
        if not has_more_lines:
            logger.info("Machine log processing complete.")
            scheduler.shutdown(wait=False)

    scheduler.add_job(
        run_monitoring,
        trigger="interval",
        minutes=1,
        id="machine_log_monitor",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    return scheduler

def main():

    configure_logging()
    scheduler = create_scheduler()
    logger.info("Machine log monitoring started (interval: 1 minute)")
    try:
        scheduler.start()

    except (KeyboardInterrupt, SystemExit):
        logger.info("Machine log monitoring stopped by user")

if __name__ == "__main__":
    main()
