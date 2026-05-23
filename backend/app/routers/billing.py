# launchkit/backend/app/routers/billing.py
import uuid

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.middleware.tenant import get_active_org_id, get_tenant_db
from app.models.user import User
from app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    SubscriptionStatusResponse,
)
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_billing_status(
    org_id: uuid.UUID = Depends(get_active_org_id),
    db: AsyncSession = Depends(get_tenant_db),
) -> SubscriptionStatusResponse:
    service = BillingService(db)
    status = await service.get_subscription_status(org_id)
    return SubscriptionStatusResponse(**status)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    body: CheckoutRequest,
    org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> CheckoutResponse:
    service = BillingService(db)
    url = await service.create_checkout_session(
        org_id=org_id,
        price_id=body.price_id,
        user_email=current_user.email,
    )
    return CheckoutResponse(checkout_url=url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    org_id: uuid.UUID = Depends(get_active_org_id),
    db: AsyncSession = Depends(get_tenant_db),
) -> PortalResponse:
    service = BillingService(db)
    url = await service.create_portal_session(org_id=org_id)
    return PortalResponse(portal_url=url)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Stripe sends events here. Signature verified inside service.
    Always returns 200 — Stripe retries on non-2xx.
    Raw body must be read before any parsing.
    """
    payload = await request.body()
    service = BillingService(db)
    return await service.handle_webhook(payload, stripe_signature)