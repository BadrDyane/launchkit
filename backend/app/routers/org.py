# launchkit/backend/app/routers/org.py
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import require_role
from app.middleware.tenant import (
    get_active_org_id,
    get_current_membership,
    get_tenant_db,
)
from app.models.membership import OrgMembership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.org import (
    AcceptInvitationRequest,
    InvitationResponse,
    InviteRequest,
    MemberResponse,
    OrgDetailResponse,
    UpdateMemberRoleRequest,
    UpdateOrgRequest,
    UserOrgResponse,
)
from app.services.invitation_service import InvitationService
from app.services.org_service import OrgService

router = APIRouter(prefix="/org", tags=["org"])


# ── Current user's org list (no tenant scope needed) ─────────────────────────

@router.get("/my-orgs", response_model=list[UserOrgResponse])
async def list_my_orgs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[UserOrgResponse]:
    service = OrgService(db)
    orgs = await service.list_user_orgs(current_user.id)
    return [UserOrgResponse(**o) for o in orgs]


# ── Org detail ────────────────────────────────────────────────────────────────

@router.get("/", response_model=OrgDetailResponse)
async def get_org(
    org_id: uuid.UUID = Depends(get_active_org_id),
    db: AsyncSession = Depends(get_tenant_db),
) -> OrgDetailResponse:
    result = await db.execute(
        select(Organization)
        .options(selectinload(Organization.plan))
        .where(Organization.id == org_id)
    )
    org = result.scalar_one()
    return OrgDetailResponse(
        id=org.id,
        name=org.name,
        subscription_status=org.subscription_status,
        stripe_customer_id=org.stripe_customer_id,
        stripe_subscription_id=org.stripe_subscription_id,
        plan_name=org.plan.name,
        plan_slug=org.plan.slug,
        ai_calls_limit=org.plan.ai_calls_limit,
        created_at=org.created_at,
    )


@router.patch("/", response_model=MessageResponse)
async def update_org(
    body: UpdateOrgRequest,
    org_id: uuid.UUID = Depends(get_active_org_id),
    membership: OrgMembership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_tenant_db),
    _: OrgMembership = require_role(50),  # admin+
) -> MessageResponse:
    service = OrgService(db)
    await service.update_org(org_id, body.name, membership)
    return MessageResponse(message="Organization updated")


# ── Members ───────────────────────────────────────────────────────────────────

@router.get("/members", response_model=list[MemberResponse])
async def list_members(
    org_id: uuid.UUID = Depends(get_active_org_id),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[MemberResponse]:
    service = OrgService(db)
    members = await service.list_members(org_id)
    return [MemberResponse(**m) for m in members]


@router.patch("/members/{user_id}/role", response_model=MessageResponse)
async def update_member_role(
    user_id: uuid.UUID,
    body: UpdateMemberRoleRequest,
    org_id: uuid.UUID = Depends(get_active_org_id),
    membership: OrgMembership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_tenant_db),
    _: OrgMembership = require_role(50),  # admin+
) -> MessageResponse:
    service = OrgService(db)
    await service.update_member_role(org_id, user_id, body.role_name, membership)
    return MessageResponse(message="Member role updated")


@router.delete("/members/{user_id}", response_model=MessageResponse)
async def remove_member(
    user_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_active_org_id),
    membership: OrgMembership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_tenant_db),
    _: OrgMembership = require_role(50),  # admin+
) -> MessageResponse:
    service = OrgService(db)
    await service.remove_member(org_id, user_id, membership)
    return MessageResponse(message="Member removed")


# ── Invitations ───────────────────────────────────────────────────────────────

@router.post("/invitations", response_model=MessageResponse)
async def invite_member(
    body: InviteRequest,
    org_id: uuid.UUID = Depends(get_active_org_id),
    membership: OrgMembership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_tenant_db),
    _: OrgMembership = require_role(50),  # admin+
) -> MessageResponse:
    org_service = OrgService(db)
    org = await org_service.get_org(org_id)

    inv_service = InvitationService(db)
    await inv_service.create_invitation(
        org_id=org_id,
        email=body.email,
        role_name=body.role_name,
        actor_membership=membership,
        org=org,
    )
    return MessageResponse(message=f"Invitation sent to {body.email}")


@router.get("/invitations", response_model=list[InvitationResponse])
async def list_invitations(
    org_id: uuid.UUID = Depends(get_active_org_id),
    db: AsyncSession = Depends(get_tenant_db),
    _: OrgMembership = require_role(50),  # admin+
) -> list[InvitationResponse]:
    service = InvitationService(db)
    invitations = await service.list_invitations(org_id)
    return [
        InvitationResponse(
            id=inv.id,
            email=inv.email,
            role_name=inv.role.name,
            status=inv.status,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
        )
        for inv in invitations
    ]


@router.delete("/invitations/{invitation_id}", response_model=MessageResponse)
async def revoke_invitation(
    invitation_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_active_org_id),
    membership: OrgMembership = Depends(get_current_membership),
    db: AsyncSession = Depends(get_tenant_db),
    _: OrgMembership = require_role(50),  # admin+
) -> MessageResponse:
    service = InvitationService(db)
    await service.revoke_invitation(invitation_id, org_id, membership)
    return MessageResponse(message="Invitation revoked")


# ── Accept invitation (no tenant scope — user may not be a member yet) ────────

@router.post("/invitations/accept", response_model=MessageResponse)
async def accept_invitation(
    body: AcceptInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = InvitationService(db)
    membership = await service.accept_invitation(body.token, current_user)
    return MessageResponse(message="Invitation accepted — you are now a member")