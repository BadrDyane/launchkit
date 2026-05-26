# launchkit/backend/app/routers/admin.py
"""
Superadmin endpoints — all protected by get_current_superadmin.
Uses get_admin_db to bypass tenant scope filter.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_admin_db
from app.middleware.auth import get_current_superadmin
from app.models.audit import AuditLog
from app.models.membership import OrgMembership
from app.models.organization import Organization
from app.models.plan import Plan
from app.models.usage import UsageCounter
from app.models.user import User
from app.schemas.admin import (
    AdminOrgResponse,
    AdminStatsResponse,
    AdminSubscriptionOverrideRequest,
    AdminUsageOverrideRequest,
    AdminUserResponse,
    AuditLogResponse,
)
from app.schemas.auth import MessageResponse
from app.services.audit_service import (
    AuditService,
    EVT_ADMIN_SUBSCRIPTION_OVERRIDE,
    EVT_ADMIN_USAGE_OVERRIDE,
    EVT_ADMIN_USER_DISABLED,
    EVT_ADMIN_USER_ENABLED,
)

router = APIRouter(prefix="/admin", tags=["admin"])


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    _=Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_admin_db),
) -> AdminStatsResponse:
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_orgs = (await db.execute(select(func.count(Organization.id)))).scalar()
    active_subs = (await db.execute(
        select(func.count(Organization.id)).where(
            Organization.subscription_status.in_(["active", "trialing"])
        )
    )).scalar()
    free_orgs = (await db.execute(
        select(func.count(Organization.id)).where(
            Organization.subscription_status == "free"
        )
    )).scalar()
    past_due = (await db.execute(
        select(func.count(Organization.id)).where(
            Organization.subscription_status == "past_due"
        )
    )).scalar()

    return AdminStatsResponse(
        total_users=total_users,
        total_orgs=total_orgs,
        active_subscriptions=active_subs,
        free_orgs=free_orgs,
        past_due_orgs=past_due,
    )


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    _=Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_admin_db),
) -> list[AdminUserResponse]:
    offset = (page - 1) * limit
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    users = result.scalars().all()
    return [AdminUserResponse.model_validate(u) for u in users]


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: uuid.UUID,
    _=Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_admin_db),
) -> AdminUserResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User not found")
    return AdminUserResponse.model_validate(user)


@router.post("/users/{user_id}/disable", response_model=MessageResponse)
async def disable_user(
    user_id: uuid.UUID,
    superadmin: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_admin_db),
) -> MessageResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User not found")

    user.is_active = False
    audit = AuditService(db)
    await audit.log(
        event_type=EVT_ADMIN_USER_DISABLED,
        actor_id=superadmin.id,
        user_id=user_id,
        target_type="user",
        target_id=str(user_id),
        metadata={"email": user.email},
    )
    await db.commit()
    return MessageResponse(message=f"User {user.email} disabled")


@router.post("/users/{user_id}/enable", response_model=MessageResponse)
async def enable_user(
    user_id: uuid.UUID,
    superadmin: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_admin_db),
) -> MessageResponse:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("User not found")

    user.is_active = True
    audit = AuditService(db)
    await audit.log(
        event_type=EVT_ADMIN_USER_ENABLED,
        actor_id=superadmin.id,
        user_id=user_id,
        target_type="user",
        target_id=str(user_id),
        metadata={"email": user.email},
    )
    await db.commit()
    return MessageResponse(message=f"User {user.email} enabled")


# ── Orgs ──────────────────────────────────────────────────────────────────────

@router.get("/orgs", response_model=list[AdminOrgResponse])
async def list_orgs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    _=Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_admin_db),
) -> list[AdminOrgResponse]:
    offset = (page - 1) * limit
    result = await db.execute(
        select(Organization)
        .options(selectinload(Organization.plan), selectinload(Organization.memberships))
        .order_by(Organization.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    orgs = result.scalars().all()

    return [
        AdminOrgResponse(
            id=o.id,
            name=o.name,
            subscription_status=o.subscription_status,
            stripe_customer_id=o.stripe_customer_id,
            stripe_subscription_id=o.stripe_subscription_id,
            plan_name=o.plan.name,
            plan_slug=o.plan.slug,
            ai_calls_limit=o.plan.ai_calls_limit,
            member_count=len([m for m in o.memberships if m.is_active]),
            created_at=o.created_at,
        )
        for o in orgs
    ]


@router.post("/orgs/{org_id}/subscription-override", response_model=MessageResponse)
async def override_subscription(
    org_id: uuid.UUID,
    body: AdminSubscriptionOverrideRequest,
    superadmin: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_admin_db),
) -> MessageResponse:
    """Manually set org plan + subscription status (e.g. for trials, comps)."""
    result = await db.execute(
        select(Organization)
        .options(selectinload(Organization.plan))
        .where(Organization.id == org_id)
    )
    org = result.scalar_one_or_none()
    if org is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError("Organization not found")

    plan_result = await db.execute(
        select(Plan).where(Plan.slug == body.plan_slug)
    )
    plan = plan_result.scalar_one_or_none()
    if plan is None:
        from app.core.exceptions import ValidationError
        raise ValidationError(f"Invalid plan slug: {body.plan_slug}")

    old_plan = org.plan.slug
    old_status = org.subscription_status

    org.plan_id = plan.id
    org.subscription_status = body.subscription_status

    audit = AuditService(db)
    await audit.log(
        event_type=EVT_ADMIN_SUBSCRIPTION_OVERRIDE,
        actor_id=superadmin.id,
        org_id=org_id,
        target_type="organization",
        target_id=str(org_id),
        metadata={
            "old_plan": old_plan,
            "new_plan": body.plan_slug,
            "old_status": old_status,
            "new_status": body.subscription_status,
        },
    )
    await db.commit()
    return MessageResponse(
        message=f"Org updated to {body.plan_slug} / {body.subscription_status}"
    )


@router.post("/orgs/{org_id}/usage-override", response_model=MessageResponse)
async def override_usage(
    org_id: uuid.UUID,
    body: AdminUsageOverrideRequest,
    superadmin: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_admin_db),
) -> MessageResponse:
    """Manually set a usage counter value (e.g. reset for a specific org)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(UsageCounter).where(
            UsageCounter.org_id == org_id,
            UsageCounter.counter_key == body.counter_key,
            UsageCounter.period_year == now.year,
            UsageCounter.period_month == now.month,
        )
    )
    counter = result.scalar_one_or_none()

    if counter is None:
        from app.core.exceptions import NotFoundError
        raise NotFoundError(
            f"No counter found for key '{body.counter_key}' in current period"
        )

    old_count = counter.count
    counter.count = body.count

    audit = AuditService(db)
    await audit.log(
        event_type=EVT_ADMIN_USAGE_OVERRIDE,
        actor_id=superadmin.id,
        org_id=org_id,
        target_type="usage_counter",
        target_id=str(counter.id),
        metadata={
            "counter_key": body.counter_key,
            "old_count": old_count,
            "new_count": body.count,
        },
    )
    await db.commit()
    return MessageResponse(message=f"Counter '{body.counter_key}' set to {body.count}")


# ── Audit log viewer ──────────────────────────────────────────────────────────

@router.get("/audit-logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    org_id: Optional[uuid.UUID] = Query(default=None),
    user_id: Optional[uuid.UUID] = Query(default=None),
    event_type: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
    _=Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_admin_db),
) -> list[AuditLogResponse]:
    offset = (page - 1) * limit
    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if org_id:
        query = query.where(AuditLog.org_id == org_id)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)

    result = await db.execute(query.offset(offset).limit(limit))
    logs = result.scalars().all()

    return [
        AuditLogResponse(
            id=log.id,
            event_type=log.event_type,
            actor_id=log.actor_id,
            user_id=log.user_id,
            org_id=log.org_id,
            target_type=log.target_type,
            target_id=log.target_id,
            metadata=log.metadata_,
            ip_address=log.ip_address,
            created_at=log.created_at,
        )
        for log in logs
    ]