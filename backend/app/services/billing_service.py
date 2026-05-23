# launchkit/backend/app/services/billing_service.py
"""
Stripe billing service.

Subscription state machine:
  free → trialing → active → past_due → canceled → expired

Key decisions:
- checkout: creates Stripe customer if not exists, links via stripe_customer_id
- webhook: all state transitions go through _apply_subscription_state()
- idempotency: stripe_events table prevents duplicate processing
- grace period: 7 days past_due before APScheduler marks expired (Phase 6)
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.exceptions import NotFoundError, ValidationError
from app.core.stripe_client import stripe
from app.models.organization import Organization
from app.models.plan import Plan
from app.models.token import StripeEvent


class BillingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_org(self, org_id: uuid.UUID) -> Organization:
        result = await self.db.execute(
            select(Organization)
            .options(selectinload(Organization.plan))
            .where(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()
        if org is None:
            raise NotFoundError("Organization not found")
        return org

    async def _get_or_create_stripe_customer(
        self,
        org: Organization,
        user_email: str,
    ) -> str:
        """Returns existing stripe_customer_id or creates a new Stripe customer."""
        if org.stripe_customer_id:
            return org.stripe_customer_id

        customer = stripe.Customer.create(
            email=user_email,
            metadata={"org_id": str(org.id)},
        )
        org.stripe_customer_id = customer["id"]
        await self.db.commit()
        return customer["id"]

    async def _get_plan_by_price_id(self, price_id: str) -> Optional[Plan]:
        result = await self.db.execute(
            select(Plan).where(Plan.stripe_price_id == price_id)
        )
        return result.scalar_one_or_none()

    async def _get_free_plan(self) -> Plan:
        result = await self.db.execute(
            select(Plan).where(Plan.slug == "free")
        )
        return result.scalar_one()

    async def _is_event_processed(self, stripe_event_id: str) -> bool:
        """Idempotency check — returns True if already processed."""
        result = await self.db.execute(
            select(StripeEvent).where(
                StripeEvent.stripe_event_id == stripe_event_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def _mark_event_processed(
        self, stripe_event_id: str, event_type: str
    ) -> None:
        self.db.add(
            StripeEvent(
                stripe_event_id=stripe_event_id,
                event_type=event_type,
            )
        )
        await self.db.commit()

    async def _get_org_by_stripe_customer(
        self, customer_id: str
    ) -> Optional[Organization]:
        result = await self.db.execute(
            select(Organization)
            .options(selectinload(Organization.plan))
            .where(Organization.stripe_customer_id == customer_id)
        )
        return result.scalar_one_or_none()

    async def _apply_subscription_state(
        self,
        org: Organization,
        *,
        status: str,
        subscription_id: Optional[str] = None,
        price_id: Optional[str] = None,
        period_end: Optional[str] = None,
    ) -> None:
        """
        Central state transition method.
        Maps Stripe subscription status → our internal status.
        Updates plan based on price_id when provided.
        """
        # Map Stripe status → our status
        stripe_to_internal = {
            "trialing": "trialing",
            "active": "active",
            "past_due": "past_due",
            "canceled": "canceled",
            "unpaid": "past_due",
            "incomplete": "past_due",
            "incomplete_expired": "expired",
            "paused": "past_due",
        }
        internal_status = stripe_to_internal.get(status, status)
        org.subscription_status = internal_status

        if subscription_id:
            org.stripe_subscription_id = subscription_id

        if period_end:
            org.subscription_current_period_end = period_end

        # Update plan based on price_id
        if price_id:
            plan = await self._get_plan_by_price_id(price_id)
            if plan:
                org.plan_id = plan.id

        # If canceled/expired → downgrade to free plan
        if internal_status in ("canceled", "expired"):
            free_plan = await self._get_free_plan()
            org.plan_id = free_plan.id
            org.stripe_subscription_id = None

        await self.db.commit()

    # ── Public methods ────────────────────────────────────────────────────────

    async def create_checkout_session(
        self,
        org_id: uuid.UUID,
        price_id: str,
        user_email: str,
    ) -> str:
        """Creates a Stripe Checkout session, returns the URL."""
        org = await self._get_org(org_id)
        customer_id = await self._get_or_create_stripe_customer(org, user_email)

        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=(
                f"{settings.FRONTEND_URL}/billing/success"
                "?session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=f"{settings.FRONTEND_URL}/billing/canceled",
            # Links Stripe session back to our org for webhook handler
            client_reference_id=str(org_id),
            subscription_data={
                "metadata": {"org_id": str(org_id)},
            },
        )
        return session["url"]

    async def create_portal_session(
        self,
        org_id: uuid.UUID,
    ) -> str:
        """Creates a Stripe Customer Portal session, returns the URL."""
        org = await self._get_org(org_id)

        if not org.stripe_customer_id:
            raise ValidationError(
                "No billing account found. Please subscribe to a plan first."
            )

        session = stripe.billing_portal.Session.create(
            customer=org.stripe_customer_id,
            return_url=f"{settings.FRONTEND_URL}/settings/billing",
        )
        return session["url"]

    async def get_subscription_status(
        self, org_id: uuid.UUID
    ) -> dict:
        org = await self._get_org(org_id)
        return {
            "org_id": org.id,
            "plan_name": org.plan.name,
            "plan_slug": org.plan.slug,
            "subscription_status": org.subscription_status,
            "ai_calls_limit": org.plan.ai_calls_limit,
            "stripe_customer_id": org.stripe_customer_id,
            "stripe_subscription_id": org.stripe_subscription_id,
        }

    # ── Webhook handlers ──────────────────────────────────────────────────────

    async def handle_webhook(
        self,
        payload: bytes,
        sig_header: str,
    ) -> dict:
        """
        Verifies Stripe webhook signature, routes to handler.
        Returns {"status": "ok"} always (Stripe expects 200).
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            raise ValidationError("Invalid webhook signature")

        event_id = event["id"]
        event_type = event["type"]

        # Idempotency — skip if already processed
        if await self._is_event_processed(event_id):
            return {"status": "ok", "skipped": True}

        # Route to handler
        handler = self._webhook_handlers.get(event_type)
        if handler:
            await handler(self, event["data"]["object"])

        await self._mark_event_processed(event_id, event_type)
        return {"status": "ok"}

    async def _handle_checkout_completed(self, obj: dict) -> None:
        """
        checkout.session.completed
        Subscription is now active. Link customer to org.
        """
        org_id_str = obj.get("client_reference_id")
        if not org_id_str:
            return

        try:
            org_id = uuid.UUID(org_id_str)
        except ValueError:
            return

        result = await self.db.execute(
            select(Organization)
            .options(selectinload(Organization.plan))
            .where(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()
        if org is None:
            return

        # Update customer_id if not already set
        customer_id = obj.get("customer")
        if customer_id and not org.stripe_customer_id:
            org.stripe_customer_id = customer_id

        subscription_id = obj.get("subscription")
        if subscription_id:
            # Fetch subscription to get price_id
            sub = stripe.Subscription.retrieve(subscription_id)
            price_id = sub["items"]["data"][0]["price"]["id"]
            period_end = str(sub["current_period_end"])

            await self._apply_subscription_state(
                org,
                status=sub["status"],
                subscription_id=subscription_id,
                price_id=price_id,
                period_end=period_end,
            )
        else:
            await self.db.commit()

    async def _handle_subscription_updated(self, obj: dict) -> None:
        """
        customer.subscription.updated
        Plan change, renewal, status change.
        """
        customer_id = obj.get("customer")
        org = await self._get_org_by_stripe_customer(customer_id)
        if org is None:
            return

        price_id = obj["items"]["data"][0]["price"]["id"]
        await self._apply_subscription_state(
            org,
            status=obj["status"],
            subscription_id=obj["id"],
            price_id=price_id,
            period_end=str(obj["current_period_end"]),
        )

    async def _handle_subscription_deleted(self, obj: dict) -> None:
        """
        customer.subscription.deleted
        Subscription canceled — downgrade to free.
        """
        customer_id = obj.get("customer")
        org = await self._get_org_by_stripe_customer(customer_id)
        if org is None:
            return

        await self._apply_subscription_state(
            org,
            status="canceled",
            subscription_id=obj["id"],
        )

    async def _handle_invoice_paid(self, obj: dict) -> None:
        """
        invoice.paid
        Successful renewal — ensure status is active.
        """
        customer_id = obj.get("customer")
        org = await self._get_org_by_stripe_customer(customer_id)
        if org is None:
            return

        subscription_id = obj.get("subscription")
        if subscription_id:
            sub = stripe.Subscription.retrieve(subscription_id)
            price_id = sub["items"]["data"][0]["price"]["id"]
            await self._apply_subscription_state(
                org,
                status="active",
                subscription_id=subscription_id,
                price_id=price_id,
                period_end=str(sub["current_period_end"]),
            )

    async def _handle_invoice_payment_failed(self, obj: dict) -> None:
        """
        invoice.payment_failed
        Move to past_due — grace period starts.
        APScheduler job (Phase 6) will expire after 7 days.
        """
        customer_id = obj.get("customer")
        org = await self._get_org_by_stripe_customer(customer_id)
        if org is None:
            return

        await self._apply_subscription_state(
            org,
            status="past_due",
        )

    async def _handle_trial_will_end(self, obj: dict) -> None:
        """
        customer.subscription.trial_will_end
        3-day warning before trial ends — no state change, just log.
        """
        # Future: send email notification
        pass

    # Webhook event → handler map
    _webhook_handlers = {
        "checkout.session.completed": _handle_checkout_completed,
        "customer.subscription.updated": _handle_subscription_updated,
        "customer.subscription.deleted": _handle_subscription_deleted,
        "invoice.paid": _handle_invoice_paid,
        "invoice.payment_failed": _handle_invoice_payment_failed,
        "customer.subscription.trial_will_end": _handle_trial_will_end,
    }