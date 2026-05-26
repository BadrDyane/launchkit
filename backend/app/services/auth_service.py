# launchkit/backend/app/services/auth_service.py
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AuthError, ConflictError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.organization import Organization
from app.models.membership import OrgMembership
from app.models.plan import Plan
from app.models.role import Role
from app.models.token import RefreshToken
from app.models.user import User
from app.services.audit_service import (
    AuditService,
    EVT_SIGNUP,
    EVT_LOGIN,
    EVT_LOGOUT,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def signup(
        self,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> tuple[User, str, str]:
        existing = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        if existing.scalar_one_or_none():
            raise ConflictError("An account with this email already exists")

        user = User(
            email=email.lower(),
            hashed_password=hash_password(password),
            display_name=display_name,
            is_email_verified=False,
        )
        self.db.add(user)
        await self.db.flush()

        free_plan = await self.db.execute(
            select(Plan).where(Plan.slug == "free")
        )
        free_plan = free_plan.scalar_one()

        org_name = f"{display_name or email.split('@')[0]}'s Workspace"
        org = Organization(
            name=org_name,
            plan_id=free_plan.id,
            subscription_status="free",
        )
        self.db.add(org)
        await self.db.flush()

        owner_role = await self.db.execute(
            select(Role).where(Role.name == "owner")
        )
        owner_role = owner_role.scalar_one()

        membership = OrgMembership(
            user_id=user.id,
            org_id=org.id,
            role_id=owner_role.id,
            is_active=True,
        )
        self.db.add(membership)

        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            is_superadmin=user.is_superadmin,
        )
        raw_refresh, refresh_hash = generate_refresh_token()
        family_id = uuid.uuid4()

        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            family_id=family_id,
            is_revoked=False,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(refresh_token)

        # Audit
        audit = AuditService(self.db)
        await audit.log(
            event_type=EVT_SIGNUP,
            actor_id=user.id,
            user_id=user.id,
            org_id=org.id,
            metadata={"email": user.email},
        )

        await self.db.commit()
        await self.db.refresh(user)
        return user, access_token, raw_refresh

    async def login(
        self,
        email: str,
        password: str,
    ) -> tuple[User, str, str]:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        user = result.scalar_one_or_none()

        if user is None or not user.hashed_password:
            verify_password("dummy", hash_password("dummy"))
            raise AuthError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthError("Invalid email or password")

        if not user.is_active:
            raise AuthError("Account is disabled")

        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            is_superadmin=user.is_superadmin,
        )
        raw_refresh, refresh_hash = generate_refresh_token()
        family_id = uuid.uuid4()

        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            family_id=family_id,
            is_revoked=False,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(refresh_token)

        # Audit
        audit = AuditService(self.db)
        await audit.log(
            event_type=EVT_LOGIN,
            actor_id=user.id,
            user_id=user.id,
            metadata={"email": user.email},
        )

        await self.db.commit()
        return user, access_token, raw_refresh

    async def refresh_tokens(
        self,
        raw_refresh_token: str,
    ) -> tuple[User, str, str]:
        token_hash = hash_token(raw_refresh_token)

        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()

        if stored is None:
            raise AuthError("Invalid refresh token")

        now = datetime.now(timezone.utc)

        if stored.is_revoked:
            await self.db.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == stored.family_id)
                .values(is_revoked=True)
            )
            await self.db.commit()
            raise AuthError("Refresh token reuse detected — please log in again")

        if stored.expires_at.replace(tzinfo=timezone.utc) < now:
            stored.is_revoked = True
            await self.db.commit()
            raise AuthError("Refresh token expired")

        stored.is_revoked = True
        await self.db.flush()

        result = await self.db.execute(
            select(User).where(User.id == stored.user_id)
        )
        user = result.scalar_one()

        if not user.is_active:
            raise AuthError("Account is disabled")

        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            is_superadmin=user.is_superadmin,
        )
        raw_new, new_hash = generate_refresh_token()

        new_refresh = RefreshToken(
            user_id=user.id,
            token_hash=new_hash,
            family_id=stored.family_id,
            is_revoked=False,
            expires_at=now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(new_refresh)
        await self.db.commit()
        return user, access_token, raw_new

    async def logout(self, raw_refresh_token: str) -> None:
        token_hash = hash_token(raw_refresh_token)
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        stored = result.scalar_one_or_none()
        if stored and not stored.is_revoked:
            stored.is_revoked = True
            await self.db.commit()