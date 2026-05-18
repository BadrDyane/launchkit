# launchkit/backend/app/models/ai_summary.py
import uuid
from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class AISummary(Base, UUIDMixin, TimestampMixin):
    """
    Output of the demo AI feature (meeting summarizer).
    Tenant-scoped — every query auto-filtered by org_id.
    """

    __tablename__ = "ai_summaries"
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
    raw_transcript: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_items: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    key_decisions: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    participants: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_in: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # relationships
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="ai_summaries"
    )

    def __repr__(self) -> str:
        return f"<AISummary org={self.org_id} cost={self.cost_usd}>"