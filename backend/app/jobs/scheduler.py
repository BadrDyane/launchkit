# launchkit/backend/app/jobs/scheduler.py
"""
APScheduler with SQLite job store.
SQLite chosen over PostgreSQL for APScheduler on Windows
(psycopg2 job store has reliability issues).

Jobs are defined here and registered at app startup.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from app.config import settings

logger = logging.getLogger(__name__)

# Single scheduler instance — shared across app lifetime
scheduler = AsyncIOScheduler(
    jobstores={
        "default": SQLAlchemyJobStore(url=settings.APSCHEDULER_SQLITE_URL)
    },
    job_defaults={
        "coalesce": True,       # Merge missed runs into one
        "max_instances": 1,     # Never run the same job twice simultaneously
        "misfire_grace_time": 3600,  # 1-hour window to catch up on missed jobs
    },
    timezone="UTC",
)


def start_scheduler() -> None:
    """Called at app startup."""
    from app.jobs.usage_reset import register_usage_reset_job
    from app.jobs.subscription_expiry import register_subscription_expiry_job

    register_usage_reset_job(scheduler)
    register_subscription_expiry_job(scheduler)

    scheduler.start()
    logger.info("APScheduler started")


def stop_scheduler() -> None:
    """Called at app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")