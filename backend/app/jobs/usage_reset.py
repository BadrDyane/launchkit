# launchkit/backend/app/jobs/usage_reset.py
"""
Runs on the 1st of every month at 00:05 UTC.
Resets usage_counters for all orgs for the previous month.
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.database import AsyncSessionLocal
from app.models.organization import Organization
from sqlalchemy import select

logger = logging.getLogger(__name__)

JOB_ID = "monthly_usage_reset"


async def run_usage_reset() -> None:
    logger.info("Starting monthly usage reset job")
    reset_count = 0

    async with AsyncSessionLocal() as db:
        try:
            # Get all orgs
            result = await db.execute(select(Organization.id))
            org_ids = result.scalars().all()

            from app.services.usage_service import UsageService
            for org_id in org_ids:
                service = UsageService(db)
                rows = await service.reset_monthly_counters(org_id)
                reset_count += rows

            logger.info(f"Usage reset complete: {reset_count} counters reset across {len(org_ids)} orgs")
        except Exception as exc:
            logger.error(f"Usage reset job failed: {exc}")


def register_usage_reset_job(scheduler: AsyncIOScheduler) -> None:
    scheduler.add_job(
        run_usage_reset,
        trigger="cron",
        day=1,
        hour=0,
        minute=5,
        id=JOB_ID,
        replace_existing=True,
    )
    logger.info(f"Registered job: {JOB_ID} (runs 1st of every month at 00:05 UTC)")