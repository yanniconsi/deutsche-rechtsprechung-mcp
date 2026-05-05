import os
import time
from loguru import logger
import schedule

from run_all import main as run_once


def _truthy(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")


RUN_ONCE = _truthy("RUN_ONCE", False)
RUN_AT = os.environ.get("RUN_AT", "03:00")


def job():
    logger.info("Pipeline job started")
    run_once()
    logger.info("Pipeline job finished")


if __name__ == "__main__":
    if RUN_ONCE:
        job()
        raise SystemExit(0)

    schedule.every().day.at(RUN_AT).do(job)
    logger.info(f"Scheduler active (daily at {RUN_AT})")

    while True:
        schedule.run_pending()
        time.sleep(1)