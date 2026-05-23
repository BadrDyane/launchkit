# launchkit/backend/app/core/stripe_client.py
"""
Thin wrapper around the Stripe SDK.
Initialized once at import time — settings already loaded.
"""
import stripe
from app.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

# Re-export stripe so callers import from here, not directly from stripe
__all__ = ["stripe"]