# launchkit/backend/app/schemas/billing.py
import uuid
from typing import Optional
from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    price_id: str  # Stripe price ID for the plan


class CheckoutResponse(BaseModel):
    checkout_url: str


class PortalResponse(BaseModel):
    portal_url: str


class SubscriptionStatusResponse(BaseModel):
    org_id: uuid.UUID
    plan_name: str
    plan_slug: str
    subscription_status: str
    ai_calls_limit: int
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]