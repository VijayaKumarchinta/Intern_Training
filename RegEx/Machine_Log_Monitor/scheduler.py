import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from jobs import monitor_machine_logs
from logging_config import configure_logging

def setup_logging():
    configure_logging()
    return logging.getLogger("scheduler")

def create_scheduler():
    scheduler = BlockingScheduler()
    scheduler.add_job(
        monitor_machine_logs,
        trigger="interval",
        minutes=1,
        id="machine_log_monitor",
        replace_existing=True
    )
    return scheduler

def start_scheduler(scheduler, logger):
    logger.info("Scheduler started")
    logger.info("Monitoring interval: 1 minute")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")

def main():
    logger = setup_logging()
    scheduler = create_scheduler()
    start_scheduler(scheduler, logger)

if __name__ == "__main__":
    main()   