# launchkit/backend/app/services/audit_service.py
"""
Append-only audit log service.

Rules:
- Never raises — catches all exceptions internally
- actor_id = who did it (may differ from user_id for admin ops)
- org_id is nullable (superadmin actions may not be org-scoped)
- The application DB user has no DELETE on audit_logs (enforced at DB level in production)
"""
import logging
import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

# ── Event type constants ──────────────────────────────────────────────────────
# Auth
EVT_SIGNUP = "user.signup"
EVT_LOGIN = "user.login"
EVT_LOGOUT = "user.logout"
EVT_PASSWORD_RESET_REQUESTED = "user.password_reset_requested"
EVT_PASSWORD_RESET_CONFIRMED = "user.password_reset_confirmed"
EVT_PASSWORD_CHANGED = "user.password_changed"
EVT_EMAIL_VERIFIED = "user.email_verified"
EVT_GOOGLE_OAUTH = "user.google_oauth"

# Org
EVT_ORG_UPDATED = "org.updated"
EVT_MEMBER_ROLE_UPDATED = "org.member_role_updated"
EVT_MEMBER_REMOVED = "org.member_removed"
EVT_INVITATION_SENT = "org.invitation_sent"
EVT_INVITATION_ACCEPTED = "org.invitation_accepted"
EVT_INVITATION_REVOKED = "org.invitation_revoked"

# Billing
EVT_CHECKOUT_INITIATED = "billing.checkout_initiated"
EVT_SUBSCRIPTION_ACTIVATED = "billing.subscription_activated"
EVT_SUBSCRIPTION_UPDATED = "billing.subscription_updated"
EVT_SUBSCRIPTION_CANCELED = "billing.subscription_canceled"
EVT_PAYMENT_FAILED = "billing.payment_failed"
EVT_SUBSCRIPTION_EXPIRED = "billing.subscription_expired"

# AI
EVT_AI_CALL = "ai.call"
EVT_AI_CALL_FAILED = "ai.call_failed"

# Admin
EVT_ADMIN_USER_DISABLED = "admin.user_disabled"
EVT_ADMIN_USER_ENABLED = "admin.user_enabled"
EVT_ADMIN_SUBSCRIPTION_OVERRIDE = "admin.subscription_override"
EVT_ADMIN_USAGE_OVERRIDE = "admin.usage_override"


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        *,
        event_type: str,
        actor_id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        org_id: Optional[uuid.UUID] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Appends an audit log entry. Never raises — all exceptions are caught.
        Call this fire-and-forget; do not await the result in a try/except.
        """
        try:
            entry = AuditLog(
                event_type=event_type,
                actor_id=actor_id,
                user_id=user_id,
                org_id=org_id,
                target_type=target_type,
                target_id=str(target_id) if target_id else None,
                metadata_=metadata,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            self.db.add(entry)
            await self.db.flush()  # Write within current transaction
        except Exception as exc:
            logger.error(f"AuditService.log failed silently: {exc}")