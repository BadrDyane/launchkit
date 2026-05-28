# launchkit/backend/app/schemas/ai.py
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class SummarizeRequest(BaseModel):
    transcript: str

    @field_validator("transcript")
    @classmethod
    def transcript_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 50:
            raise ValueError("Transcript must be at least 50 characters")
        if len(v) > 50_000:
            raise ValueError("Transcript too long (max 50,000 characters)")
        return v


class ActionItem(BaseModel):
    task: str
    owner: Optional[str] = None
    due_date: Optional[str] = None


class SummaryResponse(BaseModel):
    id: uuid.UUID
    summary: str
    action_items: list[ActionItem]
    key_decisions: list[str]
    participants: list[str]
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    created_at: datetime

    model_config = {"from_attributes": True}


class SummaryListResponse(BaseModel):
    id: uuid.UUID
    summary: str
    participants: list[str]
    cost_usd: float
    created_at: datetime

    model_config = {"from_attributes": True}