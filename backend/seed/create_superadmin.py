# launchkit/backend/seed/create_superadmin.py
"""
Run: python -m seed.create_superadmin
Creates the superadmin user for the admin panel.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password


async def main() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.email == "admin@meetingmind.app")
        )
        existing = result.scalar_one_or_none()

        if existing:
            print("Superadmin already exists")
            return

        admin = User(
            email="admin@meetingmind.app",
            hashed_password=hash_password("Demo1234!"),
            display_name="Admin User",
            is_superadmin=True,
            is_email_verified=True,
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print("Superadmin created: admin@meetingmind.app / Demo1234!")


if __name__ == "__main__":
    asyncio.run(main())