# launchkit/backend/app/models/plan.py
import uuid
from typing import Optional

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Plan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "plans"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    # -1 means unlimited
    ai_calls_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # relationships
    organizations: Mapped[list["Organization"]] = relationship(
        "Organization", back_populates="plan"
    )

    def __repr__(self) -> str:
        return f"<Plan slug={self.slug} limit={self.ai_calls_limit}>"