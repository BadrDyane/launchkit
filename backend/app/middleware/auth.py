# launchkit/backend/app/middleware/auth.py
import uuid

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency. Extracts and validates JWT, returns the User.
    Raises AuthError on any failure.
    """
    if credentials is None:
        raise AuthError("Missing authorization header")

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise AuthError("Access token expired")
    except jwt.PyJWTError:
        raise AuthError("Invalid access token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthError("Invalid token payload")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthError("Invalid token payload")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthError("User not found")

    if not user.is_active:
        raise AuthError("Account is disabled")

    return user


async def get_current_superadmin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency for superadmin-only endpoints."""
    if not current_user.is_superadmin:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("Superadmin access required")
    return current_user