# launchkit/backend/app/models/usage.py
import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class UsageCounter(Base, UUIDMixin, TimestampMixin):
    """
    Atomic counter per org per feature per month.
    Unique on (org_id, counter_key, period_year, period_month).
    """

    __tablename__ = "usage_counters"
    __table_args__ = (
        UniqueConstraint(
            "org_id",
            "counter_key",
            "period_year",
            "period_month",
            name="uq_usage_counter",
        ),
    )
    __tenant_scoped__ = True

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    counter_key: Mapped[str] = mapped_column(String(100), nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="usage_counters"
    )

    def __repr__(self) -> str:
        return (
            f"<UsageCounter org={self.org_id} key={self.counter_key} "
            f"period={self.period_year}/{self.period_month} count={self.count}>"
        )


class UsageEvent(Base, UUIDMixin, TimestampMixin):
    """
    Immutable event log per AI call — for attribution and cost reporting.
    """

    __tablename__ = "usage_events"
    __tenant_scoped__ = True

    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    counter_key: Mapped[str] = mapped_column(String(100), nullable=False)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    feature_tag: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="usage_events"
    )

    def __repr__(self) -> str:
        return f"<UsageEvent org={self.org_id} key={self.counter_key} cost={self.cost_usd}>"