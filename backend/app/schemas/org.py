# launchkit/backend/app/schemas/org.py
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class OrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    subscription_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrgDetailResponse(BaseModel):
    id: uuid.UUID
    name: str
    subscription_status: str
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    plan_name: str
    plan_slug: str
    ai_calls_limit: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateOrgRequest(BaseModel):
    name: str


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    display_name: Optional[str]
    role_name: str
    role_level: int
    is_active: bool
    joined_at: datetime

    model_config = {"from_attributes": True}


class UpdateMemberRoleRequest(BaseModel):
    role_name: str  # owner | admin | member


class InviteRequest(BaseModel):
    email: EmailStr
    role_name: str = "member"


class InvitationResponse(BaseModel):
    id: uuid.UUID
    email: str
    role_name: str
    status: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class AcceptInvitationRequest(BaseModel):
    token: str


class UserOrgResponse(BaseModel):
    """Org summary for the current user's org list."""
    id: uuid.UUID
    name: str
    role_name: str
    role_level: int
    subscription_status: str
    is_active: bool

    model_config = {"from_attributes": True}