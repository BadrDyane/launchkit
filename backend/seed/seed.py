# launchkit/backend/seed/seed.py
"""
Run: python -m seed.seed
Creates roles + plans (idempotent — safe to re-run).
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.plan import Plan
from app.models.role import Role


ROLES = [
    {"name": "owner", "level": 100},
    {"name": "admin", "level": 50},
    {"name": "member", "level": 10},
]

PLANS = [
    {
        "name": "Free",
        "slug": "free",
        "ai_calls_limit": 10,
        "price_cents": 0,
        "stripe_price_id": None,
    },
    {
        "name": "Pro",
        "slug": "pro",
        "ai_calls_limit": 100,
        "price_cents": 1500,
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID"),
    },
    {
        "name": "Business",
        "slug": "business",
        "ai_calls_limit": -1,  # unlimited
        "price_cents": 4900,
        "stripe_price_id": os.getenv("STRIPE_BUSINESS_PRICE_ID"),
    },
]


async def seed_roles(session: AsyncSession) -> None:
    for role_data in ROLES:
        result = await session.execute(
            select(Role).where(Role.name == role_data["name"])
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            session.add(Role(**role_data))
            print(f"  Created role: {role_data['name']} (level {role_data['level']})")
        else:
            print(f"  Role already exists: {role_data['name']}")
    await session.commit()


async def seed_plans(session: AsyncSession) -> None:
    for plan_data in PLANS:
        result = await session.execute(
            select(Plan).where(Plan.slug == plan_data["slug"])
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            session.add(Plan(**plan_data))
            print(f"  Created plan: {plan_data['name']} ({plan_data['ai_calls_limit']} calls/month)")
        else:
            # Update stripe_price_id if it changed
            existing.stripe_price_id = plan_data["stripe_price_id"]
            print(f"  Plan already exists: {plan_data['name']}")
    await session.commit()


async def main() -> None:
    print("=== Seeding database ===")
    async with AsyncSessionLocal() as session:
        print("\n[Roles]")
        await seed_roles(session)
        print("\n[Plans]")
        await seed_plans(session)
    print("\n=== Seed complete ===")


if __name__ == "__main__":
    asyncio.run(main())