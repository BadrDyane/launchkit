# launchkit/backend/app/models/audit.py
import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class AuditLog(Base, UUIDMixin, TimestampMixin):
    """
    Append-only audit trail. Application DB user has no DELETE on this table.
    actor_id = who performed the action (may differ from user_id for admin ops).
    """

    __tablename__ = "audit_logs"
    __tenant_scoped__ = True

    # Nullable: superadmin actions may not be scoped to an org
    org_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # The user whose data was affected
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # The user who performed the action
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        foreign_keys=[org_id],
        back_populates="audit_logs",
    )
    actor: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[actor_id],
        back_populates="audit_logs_as_actor",
    )

    def __repr__(self) -> str:
        return f"<AuditLog event={self.event_type} actor={self.actor_id}>"