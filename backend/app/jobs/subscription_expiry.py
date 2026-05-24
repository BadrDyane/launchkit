# launchkit/backend/app/jobs/subscription_expiry.py
"""
Runs every hour.
Finds orgs in past_due status for > 7 days and marks them expired,
downgrading to free plan.

7-day grace period: Stripe gives customers time to update payment before
we cut off their access. This job enforces the cutoff.
"""
import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)

JOB_ID = "subscription_expiry_check"
GRACE_PERIOD_DAYS = 7


async def run_subscription_expiry() -> None:
    grace_cutoff = datetime.now(timezone.utc) - timedelta(days=GRACE_PERIOD_DAYS)

    async with AsyncSessionLocal() as db:
        try:
            from app.models.organization import Organization
            from app.models.plan import Plan

            result = await db.execute(
                select(Organization)
                .options(selectinload(Organization.plan))
                .where(Organization.subscription_status == "past_due")
            )
            orgs = result.scalars().all()

            expired_count = 0
            for org in orgs:
                # Check if updated_at is beyond grace period
                # (updated_at changes when status moved to past_due)
                if org.updated_at.replace(tzinfo=timezone.utc) < grace_cutoff:
                    # Downgrade to free
                    free_plan = (await db.execute(
                        select(Plan).where(Plan.slug == "free")
                    )).scalar_one()

                    org.subscription_status = "expired"
                    org.plan_id = free_plan.id
                    org.stripe_subscription_id = None
                    expired_count += 1
                    logger.info(f"Org {org.id} expired after grace period — downgraded to free")

            if expired_count > 0:
                await db.commit()
                logger.info(f"Subscription expiry: {expired_count} orgs downgraded")

        except Exception as exc:
            logger.error(f"Subscription expiry job failed: {exc}")


def register_subscription_expiry_job(scheduler: AsyncIOScheduler) -> None:
    scheduler.add_job(
        run_subscription_expiry,
        trigger="interval",
        hours=1,
        id=JOB_ID,
        replace_existing=True,
    )
    logger.info(f"Registered job: {JOB_ID} (runs every hour)")