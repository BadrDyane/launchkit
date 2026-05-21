# launchkit/backend/app/services/org_service.py
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.membership import OrgMembership
from app.models.organization import Organization
from app.models.role import Role
from app.models.user import User


class OrgService:
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

    async def _count_active_owners(self, org_id: uuid.UUID) -> int:
        owner_role = await self._get_role("owner")
        result = await self.db.execute(
            select(OrgMembership).where(
                OrgMembership.org_id == org_id,
                OrgMembership.role_id == owner_role.id,
                OrgMembership.is_active == True,
            )
        )
        return len(result.scalars().all())

    # ── Org CRUD ──────────────────────────────────────────────────────────────

    async def get_org(self, org_id: uuid.UUID) -> Organization:
        result = await self.db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()
        if org is None:
            raise NotFoundError("Organization not found")
        return org

    async def update_org(
        self,
        org_id: uuid.UUID,
        name: str,
        actor_membership: OrgMembership,
    ) -> Organization:
        # Requires admin+
        if actor_membership.role.level < 50:
            raise ForbiddenError("Admin or owner required to update org settings")

        org = await self.get_org(org_id)
        org.name = name
        await self.db.commit()
        await self.db.refresh(org)
        return org

    # ── Member management ─────────────────────────────────────────────────────

    async def list_members(self, org_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(OrgMembership)
            .options(
                selectinload(OrgMembership.user),
                selectinload(OrgMembership.role),
            )
            .where(OrgMembership.org_id == org_id)
        )
        memberships = result.scalars().all()

        return [
            {
                "user_id": m.user_id,
                "email": m.user.email,
                "display_name": m.user.display_name,
                "role_name": m.role.name,
                "role_level": m.role.level,
                "is_active": m.is_active,
                "joined_at": m.created_at,
            }
            for m in memberships
        ]

    async def update_member_role(
        self,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        new_role_name: str,
        actor_membership: OrgMembership,
    ) -> OrgMembership:
        new_role = await self._get_role(new_role_name)

        # Cannot grant a role higher than your own
        if new_role.level > actor_membership.role.level:
            raise ForbiddenError("Cannot grant a role higher than your own")

        result = await self.db.execute(
            select(OrgMembership).options(selectinload(OrgMembership.role)).where(
                OrgMembership.org_id == org_id,
                OrgMembership.user_id == target_user_id,
                OrgMembership.is_active == True,
            )
        )
        target = result.scalar_one_or_none()
        if target is None:
            raise NotFoundError("Member not found")

        # Cannot demote the last owner
        if target.role.name == "owner" and new_role_name != "owner":
            owner_count = await self._count_active_owners(org_id)
            if owner_count <= 1:
                raise ForbiddenError("Cannot demote the last owner")

        target.role_id = new_role.id
        await self.db.commit()
        await self.db.refresh(target)
        return target

    async def remove_member(
        self,
        org_id: uuid.UUID,
        target_user_id: uuid.UUID,
        actor_membership: OrgMembership,
    ) -> None:
        result = await self.db.execute(
            select(OrgMembership).options(selectinload(OrgMembership.role)).where(
                OrgMembership.org_id == org_id,
                OrgMembership.user_id == target_user_id,
                OrgMembership.is_active == True,
            )
        )
        target = result.scalar_one_or_none()
        if target is None:
            raise NotFoundError("Member not found")

        # Cannot remove the last owner
        if target.role.name == "owner":
            owner_count = await self._count_active_owners(org_id)
            if owner_count <= 1:
                raise ForbiddenError("Cannot remove the last owner")

        target.is_active = False
        await self.db.commit()

    # ── User's org list ───────────────────────────────────────────────────────

    async def list_user_orgs(self, user_id: uuid.UUID) -> list[dict]:
        result = await self.db.execute(
            select(OrgMembership)
            .options(
                selectinload(OrgMembership.organization),
                selectinload(OrgMembership.role),
            )
            .where(
                OrgMembership.user_id == user_id,
                OrgMembership.is_active == True,
            )
        )
        memberships = result.scalars().all()

        return [
            {
                "id": m.organization.id,
                "name": m.organization.name,
                "role_name": m.role.name,
                "role_level": m.role.level,
                "subscription_status": m.organization.subscription_status,
                "is_active": m.is_active,
            }
            for m in memberships
        ]