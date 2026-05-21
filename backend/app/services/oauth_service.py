# launchkit/backend/app/services/oauth_service.py
"""
Google OAuth 2.0 — Authorization Code flow.
State stored in-memory with 10-minute TTL (v1 limitation — documented).
"""
import hashlib
import secrets
import time
import uuid
from typing import Optional
from urllib.parse import urlencode

import httpx

from app.config import settings
from app.core.exceptions import AuthError
from app.core.security import create_access_token, generate_refresh_token
from app.models.membership import OrgMembership
from app.models.organization import Organization
from app.models.plan import Plan
from app.models.role import Role
from app.models.token import RefreshToken
from app.models.user import User
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# In-memory state store: {state_value: (created_at_unix, redirect_to)}
_state_store: dict[str, tuple[float, str]] = {}
_STATE_TTL = 600  # 10 minutes


def _prune_states() -> None:
    now = time.time()
    expired = [k for k, (ts, _) in _state_store.items() if now - ts > _STATE_TTL]
    for k in expired:
        del _state_store[k]


def generate_oauth_state(redirect_to: str = "/dashboard") -> str:
    """Creates a CSRF state token, stores it, returns it."""
    _prune_states()
    state = secrets.token_urlsafe(32)
    _state_store[state] = (time.time(), redirect_to)
    return state


def validate_oauth_state(state: str) -> str:
    """
    Validates state exists and is not expired.
    Returns redirect_to URL.
    Raises AuthError on failure.
    """
    _prune_states()
    entry = _state_store.pop(state, None)
    if entry is None:
        raise AuthError("Invalid or expired OAuth state")
    created_at, redirect_to = entry
    if time.time() - created_at > _STATE_TTL:
        raise AuthError("OAuth state expired")
    return redirect_to


def build_google_auth_url(state: str) -> str:
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    """Exchanges authorization code for Google access/id tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise AuthError("Failed to exchange OAuth code")
    return resp.json()


async def get_google_user_info(access_token: str) -> dict:
    """Fetches user profile from Google."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
    if resp.status_code != 200:
        raise AuthError("Failed to fetch Google user info")
    return resp.json()


async def upsert_google_user(
    db: AsyncSession,
    google_id: str,
    email: str,
    display_name: Optional[str],
    avatar_url: Optional[str],
) -> tuple[User, str, str]:
    """
    Finds existing user by google_id or email, links Google account,
    or creates new user + org. Returns (user, access_token, raw_refresh).
    """
    # Try by google_id first
    result = await db.execute(
        select(User).where(User.google_id == google_id)
    )
    user = result.scalar_one_or_none()

    # Try by email (link existing account)
    if user is None:
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()
        if user:
            user.google_id = google_id
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url

    # Create new user
    if user is None:
        user = User(
            email=email.lower(),
            google_id=google_id,
            display_name=display_name,
            avatar_url=avatar_url,
            is_email_verified=True,  # Google verifies email
            hashed_password=None,
        )
        db.add(user)
        await db.flush()

        # Default org
        free_plan = (await db.execute(
            select(Plan).where(Plan.slug == "free")
        )).scalar_one()

        org = Organization(
            name=f"{display_name or email.split('@')[0]}'s Workspace",
            plan_id=free_plan.id,
            subscription_status="free",
        )
        db.add(org)
        await db.flush()

        owner_role = (await db.execute(
            select(Role).where(Role.name == "owner")
        )).scalar_one()

        db.add(OrgMembership(
            user_id=user.id,
            org_id=org.id,
            role_id=owner_role.id,
            is_active=True,
        ))

    # Issue tokens
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        is_superadmin=user.is_superadmin,
    )
    raw_refresh, refresh_hash = generate_refresh_token()

    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        family_id=uuid.uuid4(),
        is_revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        ),
    ))

    await db.commit()
    await db.refresh(user)
    return user, access_token, raw_refresh