# launchkit/backend/app/schemas/usage.py
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UsageCounterResponse(BaseModel):
    org_id: uuid.UUID
    counter_key: str
    period_year: int
    period_month: int
    count: int
    limit: int  # -1 = unlimited
    is_unlimited: bool
    remaining: Optional[int]  # None if unlimited

    model_config = {"from_attributes": True}


class UsageSummaryResponse(BaseModel):
    org_id: uuid.UUID
    plan_name: str
    ai_calls_used: int
    ai_calls_limit: int
    is_unlimited: bool
    remaining: Optional[int]
    period_year: int
    period_month: int