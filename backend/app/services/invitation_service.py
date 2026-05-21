# launchkit/backend/app/services/invitation_service.py
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import send_email
from app.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.membership import Invitation, OrgMembership
from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User

_INVITE_TTL = timedelta(days=7)


def _generate_token() -> tuple[str, str]:
    raw = secrets.token_bytes(32)
    raw_hex = raw.hex()
    token_hash = hashlib.sha256(raw).hexdigest()
    return raw_hex, token_hash


def _send_invitation_email(to: str, org_name: str, raw_token: str) -> None:
    accept_url = f"{settings.FRONTEND_URL}/invitations/accept?token={raw_token}"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>You've been invited to {org_name}</h2>
        <p>Click below to accept the invitation. This link expires in 7 days.</p>
        <a href="{accept_url}" style="
            display: inline-block;
            padding: 12px 24px;
            background: #00C896;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin: 16px 0;
        ">Accept Invitation</a>
        <p style="color: #888;">If you didn't expect this, ignore this email.</p>
    </div>
    """
    send_email(to, f"You've been invited to {org_name} — MeetingMind", html)


class InvitationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_role(self, name: str) -> Role:
        result = await self.db.execute(
            select(Role).where(Role.name == name)
        )
        role = result.scalar_one_or_none()
        if role is None:
            raise ValidationError(f"Invalid role: {name}")
        return role

    async def create_invitation(
        self,
        org_id: uuid.UUID,
        email: str,
        role_name: str,
        actor_membership: OrgMembership,
        org: Organization,
    ) -> Invitation:
        role = await self._get_role(role_name)

        # Cannot invite to a role higher than your own
        if role.level > actor_membership.role.level:
            raise ForbiddenError("Cannot invite to a role higher than your own")

        # Check for existing active membership
        existing_member = await self.db.execute(
            select(OrgMembership)
            .join(User, OrgMembership.user_id == User.id)
            .where(
                OrgMembership.org_id == org_id,
                User.email == email.lower(),
                OrgMembership.is_active == True,
            )
        )
        if existing_member.scalar_one_or_none():
            raise ConflictError("User is already a member of this organization")

        # Check for existing pending invitation
        existing_invite = await self.db.execute(
            select(Invitation).where(
                Invitation.org_id == org_id,
                Invitation.email == email.lower(),
                Invitation.status == "pending",
            )
        )
        if existing_invite.scalar_one_or_none():
            raise ConflictError("A pending invitation already exists for this email")

        raw, token_hash = _generate_token()

        invitation = Invitation(
            org_id=org_id,
            email=email.lower(),
            role_id=role.id,
            token_hash=token_hash,
            status="pending",
            expires_at=datetime.now(timezone.utc) + _INVITE_TTL,
            invited_by_id=actor_membership.user_id,
        )
        self.db.add(invitation)
        await self.db.commit()
        await self.db.refresh(invitation)

        _send_invitation_email(email, org.name, raw)
        return invitation

    async def list_invitations(self, org_id: uuid.UUID) -> list[Invitation]:
        result = await self.db.execute(
            select(Invitation)
            .options(selectinload(Invitation.role))
            .where(
                Invitation.org_id == org_id,
                Invitation.status == "pending",
            )
        )
        return result.scalars().all()

    async def accept_invitation(
        self,
        raw_token: str,
        current_user: User,
    ) -> OrgMembership:
        token_hash = hashlib.sha256(bytes.fromhex(raw_token)).hexdigest()
        now = datetime.now(timezone.utc)

        result = await self.db.execute(
            select(Invitation).options(selectinload(Invitation.role)).where(
                Invitation.token_hash == token_hash
            )
        )
        invitation = result.scalar_one_or_none()

        if invitation is None:
            raise ValidationError("Invalid invitation token")
        if invitation.status != "pending":
            raise ValidationError(f"Invitation is already {invitation.status}")
        if invitation.expires_at.replace(tzinfo=timezone.utc) < now:
            invitation.status = "expired"
            await self.db.commit()
            raise ValidationError("Invitation has expired")
        if invitation.email != current_user.email:
            raise ForbiddenError("This invitation was sent to a different email address")

        # Check if already a member
        existing = await self.db.execute(
            select(OrgMembership).where(
                OrgMembership.org_id == invitation.org_id,
                OrgMembership.user_id == current_user.id,
            )
        )
        existing_membership = existing.scalar_one_or_none()

        if existing_membership:
            if existing_membership.is_active:
                raise ConflictError("You are already a member of this organization")
            # Reactivate
            existing_membership.is_active = True
            existing_membership.role_id = invitation.role_id
            membership = existing_membership
        else:
            membership = OrgMembership(
                user_id=current_user.id,
                org_id=invitation.org_id,
                role_id=invitation.role_id,
                is_active=True,
            )
            self.db.add(membership)

        invitation.status = "accepted"
        await self.db.commit()
        await self.db.refresh(membership)
        return membership

    async def revoke_invitation(
        self,
        invitation_id: uuid.UUID,
        org_id: uuid.UUID,
        actor_membership: OrgMembership,
    ) -> None:
        result = await self.db.execute(
            select(Invitation).where(
                Invitation.id == invitation_id,
                Invitation.org_id == org_id,
            )
        )
        invitation = result.scalar_one_or_none()
        if invitation is None:
            raise NotFoundError("Invitation not found")
        if invitation.status != "pending":
            raise ValidationError("Only pending invitations can be revoked")

        invitation.status = "revoked"
        await self.db.commit()