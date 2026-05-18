# launchkit/backend/app/models/organization.py
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class Organization(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Stripe
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    # Subscription state machine:
    # free → trialing → active → past_due → canceled → expired
    subscription_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free"
    )
    subscription_current_period_end: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Plan FK
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="RESTRICT"),
        nullable=False,
    )

    # relationships
    plan: Mapped["Plan"] = relationship("Plan", back_populates="organizations")
    memberships: Mapped[list["OrgMembership"]] = relationship(
        "OrgMembership", back_populates="organization", cascade="all, delete-orphan"
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation", back_populates="organization", cascade="all, delete-orphan"
    )
    usage_counters: Mapped[list["UsageCounter"]] = relationship(
        "UsageCounter", back_populates="organization", cascade="all, delete-orphan"
    )
    usage_events: Mapped[list["UsageEvent"]] = relationship(
        "UsageEvent", back_populates="organization", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        foreign_keys="AuditLog.org_id",
        back_populates="organization",
    )
    ai_summaries: Mapped[list["AISummary"]] = relationship(
        "AISummary", back_populates="organization", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Organization name={self.name} status={self.subscription_status}>"