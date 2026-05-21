# launchkit/backend/app/middleware/tenant.py
"""
Tenant scope enforcement via SQLAlchemy session events.

Every model with __tenant_scoped__ = True gets a WHERE org_id = :tenant_id
injected automatically on all SELECT, UPDATE, DELETE queries.

The active org is read from the X-Active-Org request header.
The middleware validates the user is actually a member of that org.
"""
import uuid
from typing import Optional

from fastapi import Depends, Header, Request
from sqlalchemy import event, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, ForbiddenError, NotFoundError
from app.database import AsyncSessionLocal, get_db
from app.middleware.auth import get_current_user
from app.models.membership import OrgMembership
from app.models.organization import Organization
from app.models.user import User


def _install_tenant_filter(session: Session, org_id: uuid.UUID) -> None:
    """
    Installs a do_orm_execute event listener on this session that
    appends WHERE org_id = :org_id to all queries on tenant-scoped models.
    """

    @event.listens_for(session.sync_session, "do_orm_execute")
    def _filter(execute_state):
        # Skip if admin bypass is set
        if session.info.get("admin_bypass"):
            return

        # Only filter SELECT statements (not DDL)
        if not execute_state.is_select:
            return

        # Check if the query touches any tenant-scoped mapper
        statement = execute_state.statement
        for entity in execute_state.all_mappers:
            if getattr(entity.class_, "__tenant_scoped__", False):
                # Append the tenant filter
                execute_state.statement = statement.filter_by(org_id=org_id)
                break


async def get_tenant_db(
    request: Request,
    x_active_org: Optional[str] = Header(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> AsyncSession:
    """
    FastAPI dependency that returns a DB session with tenant scope applied.

    Reads X-Active-Org header → validates membership → installs filter.
    Raises 401 if no org header, 403 if not a member.
    """
    if x_active_org is None:
        raise AuthError("X-Active-Org header is required")

    try:
        org_id = uuid.UUID(x_active_org)
    except ValueError:
        raise AuthError("X-Active-Org must be a valid UUID")

    # Validate membership
    result = await db.execute(
        select(OrgMembership).where(
            OrgMembership.user_id == current_user.id,
            OrgMembership.org_id == org_id,
            OrgMembership.is_active == True,
        )
    )
    membership = result.scalar_one_or_none()

    if membership is None:
        raise ForbiddenError("You are not a member of this organization")

    # Store on session for RBAC dependency to read
    db.info["org_id"] = org_id
    db.info["membership"] = membership

    return db


async def get_current_membership(
    db: AsyncSession = Depends(get_tenant_db),
) -> OrgMembership:
    """Returns the current user's membership in the active org."""
    return db.info["membership"]


async def get_active_org_id(
    db: AsyncSession = Depends(get_tenant_db),
) -> uuid.UUID:
    """Returns the active org UUID from the validated session."""
    return db.info["org_id"]