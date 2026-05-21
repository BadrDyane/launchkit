# launchkit/backend/app/middleware/rbac.py
from fastapi import Depends

from app.core.exceptions import ForbiddenError
from app.middleware.tenant import get_current_membership
from app.models.membership import OrgMembership


def require_role(minimum_level: int):
    """
    Returns a FastAPI dependency that enforces a minimum role level.

    Usage:
        @router.delete("/org", dependencies=[Depends(require_role(100))])
        async def delete_org(...):
            ...

    Levels: owner=100, admin=50, member=10
    """

    async def _check(
        membership: OrgMembership = Depends(get_current_membership),
    ) -> OrgMembership:
        if membership.role.level < minimum_level:
            raise ForbiddenError(
                f"This action requires a higher role level ({minimum_level} required, "
                f"you have {membership.role.level})"
            )
        return membership

    return Depends(_check)