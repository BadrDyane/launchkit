# launchkit/backend/app/services/usage_service.py
"""
Usage metering service.

Key design: atomic pre-flight check via conditional UPDATE.

    UPDATE usage_counters
    SET count = count + 1
    WHERE org_id = :org_id
      AND counter_key = :key
      AND period_year = :year
      AND period_month = :month
      AND (count < :limit OR :limit = -1)
    RETURNING count

0 rows updated = limit reached → raise HTTP 402.
This is atomic — no race conditions possible.

If the AI call fails after increment → compensating decrement (best-effort).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.core.exceptions import UsageLimitError
from app.models.organization import Organization
from app.models.plan import Plan
from app.models.usage import UsageCounter, UsageEvent
from sqlalchemy.orm import selectinload

# Counter key for AI summarization calls
AI_CALLS_KEY = "ai_calls"


class UsageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_org_with_plan(self, org_id: uuid.UUID) -> Organization:
        result = await self.db.execute(
            select(Organization)
            .options(selectinload(Organization.plan))
            .where(Organization.id == org_id)
        )
        return result.scalar_one()

    async def _ensure_counter_exists(
        self,
        org_id: uuid.UUID,
        counter_key: str,
        year: int,
        month: int,
    ) -> None:
        """
        Upsert the counter row so the atomic UPDATE has a row to hit.
        INSERT ... ON CONFLICT DO NOTHING — idempotent.
        """
        stmt = insert(UsageCounter).values(
            org_id=org_id,
            counter_key=counter_key,
            period_year=year,
            period_month=month,
            count=0,
        ).on_conflict_do_nothing(
            index_elements=["org_id", "counter_key", "period_year", "period_month"]
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def check_and_increment(
        self,
        org_id: uuid.UUID,
        counter_key: str = AI_CALLS_KEY,
        upgrade_url: str = "/settings/billing",
    ) -> int:
        """
        Atomic pre-flight check + increment.
        Returns the new count on success.
        Raises UsageLimitError (HTTP 402) if limit reached.
        """
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month

        org = await self._get_org_with_plan(org_id)
        limit = org.plan.ai_calls_limit  # -1 = unlimited

        # Ensure the counter row exists
        await self._ensure_counter_exists(org_id, counter_key, year, month)

        # Atomic conditional increment
        if limit == -1:
            # Unlimited — just increment, no condition
            result = await self.db.execute(
                text("""
                    UPDATE usage_counters
                    SET count = count + 1,
                        updated_at = NOW()
                    WHERE org_id = :org_id
                      AND counter_key = :key
                      AND period_year = :year
                      AND period_month = :month
                    RETURNING count
                """),
                {
                    "org_id": str(org_id),
                    "key": counter_key,
                    "year": year,
                    "month": month,
                },
            )
        else:
            # Conditional — only increment if under limit
            result = await self.db.execute(
                text("""
                    UPDATE usage_counters
                    SET count = count + 1,
                        updated_at = NOW()
                    WHERE org_id = :org_id
                      AND counter_key = :key
                      AND period_year = :year
                      AND period_month = :month
                      AND count < :limit
                    RETURNING count
                """),
                {
                    "org_id": str(org_id),
                    "key": counter_key,
                    "year": year,
                    "month": month,
                    "limit": limit,
                },
            )

        row = result.fetchone()

        if row is None:
            # 0 rows updated = limit reached
            raise UsageLimitError(
                detail=f"You've reached your monthly limit of {limit} AI calls. Upgrade to continue.",
                upgrade_url=upgrade_url,
            )

        await self.db.commit()
        return row[0]

    async def decrement(
        self,
        org_id: uuid.UUID,
        counter_key: str = AI_CALLS_KEY,
    ) -> None:
        """
        Compensating decrement when AI call fails after increment.
        Best-effort — never raises.
        """
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month
        try:
            await self.db.execute(
                text("""
                    UPDATE usage_counters
                    SET count = GREATEST(count - 1, 0),
                        updated_at = NOW()
                    WHERE org_id = :org_id
                      AND counter_key = :key
                      AND period_year = :year
                      AND period_month = :month
                """),
                {
                    "org_id": str(org_id),
                    "key": counter_key,
                    "year": year,
                    "month": month,
                },
            )
            await self.db.commit()
        except Exception:
            pass  # Best-effort only

    async def log_usage_event(
        self,
        org_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        counter_key: str,
        tokens_used: int,
        cost_usd: float,
        model: str,
        feature_tag: str,
    ) -> None:
        """Appends an immutable usage event for cost attribution."""
        event = UsageEvent(
            org_id=org_id,
            user_id=user_id,
            counter_key=counter_key,
            tokens_used=tokens_used,
            cost_usd=cost_usd,
            model=model,
            feature_tag=feature_tag,
        )
        self.db.add(event)
        await self.db.commit()

    async def get_current_usage(
        self,
        org_id: uuid.UUID,
        counter_key: str = AI_CALLS_KEY,
    ) -> dict:
        """Returns current usage stats for the active billing period."""
        now = datetime.now(timezone.utc)
        year, month = now.year, now.month

        org = await self._get_org_with_plan(org_id)
        limit = org.plan.ai_calls_limit

        result = await self.db.execute(
            select(UsageCounter).where(
                UsageCounter.org_id == org_id,
                UsageCounter.counter_key == counter_key,
                UsageCounter.period_year == year,
                UsageCounter.period_month == month,
            )
        )
        counter = result.scalar_one_or_none()
        count = counter.count if counter else 0

        return {
            "org_id": org_id,
            "plan_name": org.plan.name,
            "ai_calls_used": count,
            "ai_calls_limit": limit,
            "is_unlimited": limit == -1,
            "remaining": None if limit == -1 else max(0, limit - count),
            "period_year": year,
            "period_month": month,
        }

    async def reset_monthly_counters(self, org_id: uuid.UUID) -> int:
        """
        Resets all counters for the previous month to 0.
        Called by APScheduler on the 1st of each month.
        Returns number of rows reset.
        """
        now = datetime.now(timezone.utc)
        # Reset previous month
        if now.month == 1:
            year, month = now.year - 1, 12
        else:
            year, month = now.year, now.month - 1

        result = await self.db.execute(
            text("""
                UPDATE usage_counters
                SET count = 0, updated_at = NOW()
                WHERE org_id = :org_id
                  AND period_year = :year
                  AND period_month = :month
            """),
            {"org_id": str(org_id), "year": year, "month": month},
        )
        await self.db.commit()
        return result.rowcount