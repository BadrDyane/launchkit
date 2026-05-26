# launchkit/backend/app/schemas/admin.py
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AdminUserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: Optional[str]
    is_superadmin: bool
    is_email_verified: bool
    is_active: bool
    google_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminOrgResponse(BaseModel):
    id: uuid.UUID
    name: str
    subscription_status: str
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    plan_name: str
    plan_slug: str
    ai_calls_limit: int
    member_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminSubscriptionOverrideRequest(BaseModel):
    plan_slug: str
    subscription_status: str


class AdminUsageOverrideRequest(BaseModel):
    counter_key: str
    count: int


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    actor_id: Optional[uuid.UUID]
    user_id: Optional[uuid.UUID]
    org_id: Optional[uuid.UUID]
    target_type: Optional[str]
    target_id: Optional[str]
    metadata: Optional[dict]
    ip_address: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminStatsResponse(BaseModel):
    total_users: int
    total_orgs: int
    active_subscriptions: int
    free_orgs: int
    past_due_orgs: int