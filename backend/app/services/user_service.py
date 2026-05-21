# launchkit/backend/app/services/user_service.py
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_email_verification, send_password_reset
from app.core.exceptions import AuthError, NotFoundError, ValidationError
from app.core.security import hash_password, verify_password
from app.models.token import EmailVerificationToken, PasswordResetToken
from app.models.user import User

_1_HOUR = timedelta(hours=1)
_24_HOURS = timedelta(hours=24)


def _generate_token() -> tuple[str, str]:
    """Returns (raw_hex, sha256_hash)."""
    raw = secrets.token_bytes(32)
    raw_hex = raw.hex()
    token_hash = hashlib.sha256(raw).hexdigest()
    return raw_hex, token_hash


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Email verification ────────────────────────────────────────────────────

    async def send_verification_email(self, user: User) -> None:
        """Issues a new email verification token and sends the email."""
        raw, token_hash = _generate_token()

        record = EmailVerificationToken(
            user_id=user.id,
            token_hash=token_hash,
            is_used=False,
            expires_at=datetime.now(timezone.utc) + _24_HOURS,
        )
        self.db.add(record)
        await self.db.commit()

        # Fire-and-forget — email service never raises
        send_email_verification(user.email, raw)

    async def verify_email(self, raw_token: str) -> User:
        """Marks the token used and sets user.is_email_verified = True."""
        token_hash = hashlib.sha256(bytes.fromhex(raw_token)).hexdigest()
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(EmailVerificationToken).where(
                EmailVerificationToken.token_hash == token_hash
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            raise ValidationError("Invalid verification token")
        if record.is_used:
            raise ValidationError("Token already used")
        if record.expires_at.replace(tzinfo=timezone.utc) < now:
            raise ValidationError("Verification token expired")

        record.is_used = True

        result = await self.db.execute(
            select(User).where(User.id == record.user_id)
        )
        user = result.scalar_one()
        user.is_email_verified = True

        await self.db.commit()
        await self.db.refresh(user)
        return user

    # ── Password reset ────────────────────────────────────────────────────────

    async def request_password_reset(self, email: str) -> None:
        """
        Always returns 200 regardless of whether email exists —
        prevents user enumeration.
        """
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            # Silent return — don't reveal whether email exists
            return

        raw, token_hash = _generate_token()

        record = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            is_used=False,
            expires_at=datetime.now(timezone.utc) + _1_HOUR,
        )
        self.db.add(record)
        await self.db.commit()

        send_password_reset(user.email, raw)

    async def confirm_password_reset(
        self,
        raw_token: str,
        new_password: str,
    ) -> None:
        """Validates token, updates password, marks token used."""
        token_hash = hashlib.sha256(bytes.fromhex(raw_token)).hexdigest()
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash
            )
        )
        record = result.scalar_one_or_none()

        if record is None:
            raise ValidationError("Invalid or expired reset token")
        if record.is_used:
            raise ValidationError("Token already used")
        if record.expires_at.replace(tzinfo=timezone.utc) < now:
            raise ValidationError("Reset token expired")

        # Mark used immediately — prevents replay
        record.is_used = True
        await self.db.flush()

        result = await self.db.execute(
            select(User).where(User.id == record.user_id)
        )
        user = result.scalar_one()
        user.hashed_password = hash_password(new_password)

        await self.db.commit()

    # ── Change password (authenticated) ──────────────────────────────────────

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        if not user.hashed_password:
            raise ValidationError("OAuth accounts cannot change password here")
        if not verify_password(current_password, user.hashed_password):
            raise AuthError("Current password is incorrect")
        user.hashed_password = hash_password(new_password)
        await self.db.commit()