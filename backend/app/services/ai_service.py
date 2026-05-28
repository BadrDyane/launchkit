# launchkit/backend/app/services/ai_service.py
"""
Meeting summarizer — canonical AI feature pattern for LaunchKit.

Every AI feature in this codebase follows this template:
1. Pre-flight usage check (atomic increment or 402)
2. LLM call with structured output schema
3. Validate / parse response
4. Store result (tenant-scoped)
5. Log usage event (cost attribution)
6. If LLM call fails → compensating decrement

This pattern ensures:
- Usage is always metered before AI runs
- Cost is always tracked
- Output is always schema-validated
- Tenant isolation is enforced by the DB session
"""
import json
import logging
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.openai_client import (
    calculate_cost,
    chat_completion,
    extract_text,
    extract_usage,
)
from app.config import settings
from app.models.ai_summary import AISummary
from app.services.audit_service import AuditService, EVT_AI_CALL, EVT_AI_CALL_FAILED
from app.services.usage_service import AI_CALLS_KEY, UsageService

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an expert meeting analyst. Your job is to analyze meeting transcripts and extract structured information.

Always respond with valid JSON matching this exact schema:
{
  "summary": "2-4 sentence overview of the meeting",
  "action_items": [
    {"task": "description", "owner": "person name or null", "due_date": "date string or null"}
  ],
  "key_decisions": ["decision 1", "decision 2"],
  "participants": ["name1", "name2"]
}

Rules:
- summary: concise, factual, 2-4 sentences
- action_items: concrete tasks with clear owners when mentioned
- key_decisions: major decisions made, not discussion points
- participants: names mentioned or identifiable from context
- Respond ONLY with the JSON object — no preamble, no markdown fences"""


class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def summarize_transcript(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        transcript: str,
    ) -> AISummary:
        """
        Full pipeline:
        1. Pre-flight check (402 if limit reached)
        2. OpenAI call
        3. Parse + validate JSON output
        4. Store AISummary
        5. Log usage event
        6. Compensating decrement if step 2-4 fail
        """
        usage_service = UsageService(self.db)
        audit_service = AuditService(self.db)
        model = settings.OPENAI_DEFAULT_MODEL

        # Step 1 — atomic pre-flight check + increment
        await usage_service.check_and_increment(
            org_id=org_id,
            counter_key=AI_CALLS_KEY,
            upgrade_url="/settings/billing",
        )

        tokens_in = tokens_out = 0
        cost_usd = 0.0

        try:
            # Step 2 — LLM call
            response = await chat_completion(
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": f"Transcript:\n\n{transcript}"},
                ],
                model=model,
                temperature=0.2,
                max_tokens=1500,
            )

            tokens_in, tokens_out = extract_usage(response)
            cost_usd = calculate_cost(model, tokens_in, tokens_out)
            raw_text = extract_text(response)

            # Step 3 — Parse + validate JSON
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                # Retry once with corrective prompt
                logger.warning("AI returned invalid JSON — retrying with correction")
                retry_response = await chat_completion(
                    messages=[
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user", "content": f"Transcript:\n\n{transcript}"},
                        {"role": "assistant", "content": raw_text},
                        {
                            "role": "user",
                            "content": "Your response was not valid JSON. Please respond with only the JSON object, no other text.",
                        },
                    ],
                    model=model,
                    temperature=0.1,
                    max_tokens=1500,
                )
                r_in, r_out = extract_usage(retry_response)
                tokens_in += r_in
                tokens_out += r_out
                cost_usd = calculate_cost(model, tokens_in, tokens_out)
                raw_text = extract_text(retry_response)
                parsed = json.loads(raw_text)

            # Validate required fields
            if "summary" not in parsed:
                raise ValidationError("AI response missing required 'summary' field")

            # Step 4 — Store result (tenant-scoped via session)
            summary = AISummary(
                org_id=org_id,
                user_id=user_id,
                raw_transcript=transcript,
                summary=parsed.get("summary", ""),
                action_items=parsed.get("action_items", []),
                key_decisions=parsed.get("key_decisions", []),
                participants=parsed.get("participants", []),
                model=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=cost_usd,
            )
            self.db.add(summary)
            await self.db.flush()

            # Step 5 — Log usage event
            await usage_service.log_usage_event(
                org_id=org_id,
                user_id=user_id,
                counter_key=AI_CALLS_KEY,
                tokens_used=tokens_in + tokens_out,
                cost_usd=cost_usd,
                model=model,
                feature_tag="meeting_summarizer",
            )

            # Audit
            await audit_service.log(
                event_type=EVT_AI_CALL,
                actor_id=user_id,
                user_id=user_id,
                org_id=org_id,
                target_type="ai_summary",
                target_id=str(summary.id),
                metadata={
                    "model": model,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                    "cost_usd": round(cost_usd, 6),
                    "feature": "meeting_summarizer",
                },
            )

            await self.db.commit()
            await self.db.refresh(summary)
            return summary

        except Exception as exc:
            # Step 6 — Compensating decrement (best-effort)
            await usage_service.decrement(org_id=org_id, counter_key=AI_CALLS_KEY)

            # Audit failure
            try:
                await audit_service.log(
                    event_type=EVT_AI_CALL_FAILED,
                    actor_id=user_id,
                    user_id=user_id,
                    org_id=org_id,
                    metadata={"error": str(exc), "feature": "meeting_summarizer"},
                )
                await self.db.commit()
            except Exception:
                pass

            raise

    async def list_summaries(
        self,
        org_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
    ) -> list[AISummary]:
        """Lists summaries for the active org (tenant-scoped automatically)."""
        offset = (page - 1) * limit
        result = await self.db.execute(
            select(AISummary)
            .where(AISummary.org_id == org_id)
            .order_by(AISummary.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_summary(
        self,
        summary_id: uuid.UUID,
        org_id: uuid.UUID,
    ) -> AISummary:
        result = await self.db.execute(
            select(AISummary).where(
                AISummary.id == summary_id,
                AISummary.org_id == org_id,
            )
        )
        summary = result.scalar_one_or_none()
        if summary is None:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("Summary not found")
        return summary