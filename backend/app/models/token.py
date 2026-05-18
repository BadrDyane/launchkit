# launchkit/backend/app/models/token.py
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class RefreshToken(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # SHA-256 of the raw 32-byte token sent to client
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    # All tokens in a family share one family_id (theft detection)
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    is_revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    def __repr__(self) -> str:
        return f"<RefreshToken user={self.user_id} revoked={self.is_revoked}>"


class PasswordResetToken(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "password_reset_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 1-hour expiry
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="password_reset_tokens"
    )

    def __repr__(self) -> str:
        return f"<PasswordResetToken user={self.user_id} used={self.is_used}>"


class EmailVerificationToken(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "email_verification_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True
    )
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # 24-hour expiry
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="email_verification_tokens"
    )

    def __repr__(self) -> str:
        return f"<EmailVerificationToken user={self.user_id} used={self.is_used}>"


class StripeEvent(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "stripe_events"

    # Unique constraint on stripe's event ID — idempotency store
    stripe_event_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)

    def __repr__(self) -> str:
        return f"<StripeEvent id={self.stripe_event_id}>"