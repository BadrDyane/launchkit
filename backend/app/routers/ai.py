# launchkit/backend/app/routers/ai.py
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import get_current_user
from app.middleware.tenant import get_active_org_id, get_tenant_db
from app.models.user import User
from app.schemas.ai import SummarizeRequest, SummaryListResponse, SummaryResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/summarize", response_model=SummaryResponse, status_code=201)
async def summarize(
    body: SummarizeRequest,
    org_id: uuid.UUID = Depends(get_active_org_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_tenant_db),
) -> SummaryResponse:
    """
    Summarizes a meeting transcript.
    Pre-flight usage check enforced — returns 402 if limit reached.
    """
    service = AIService(db)
    summary = await service.summarize_transcript(
        org_id=org_id,
        user_id=current_user.id,
        transcript=body.transcript,
    )
    return SummaryResponse(
        id=summary.id,
        summary=summary.summary,
        action_items=summary.action_items or [],
        key_decisions=summary.key_decisions or [],
        participants=summary.participants or [],
        model=summary.model,
        tokens_in=summary.tokens_in,
        tokens_out=summary.tokens_out,
        cost_usd=summary.cost_usd,
        created_at=summary.created_at,
    )


@router.get("/summaries", response_model=list[SummaryListResponse])
async def list_summaries(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    org_id: uuid.UUID = Depends(get_active_org_id),
    db: AsyncSession = Depends(get_tenant_db),
) -> list[SummaryListResponse]:
    service = AIService(db)
    summaries = await service.list_summaries(org_id, page, limit)
    return [
        SummaryListResponse(
            id=s.id,
            summary=s.summary,
            participants=s.participants or [],
            cost_usd=s.cost_usd,
            created_at=s.created_at,
        )
        for s in summaries
    ]


@router.get("/summaries/{summary_id}", response_model=SummaryResponse)
async def get_summary(
    summary_id: uuid.UUID,
    org_id: uuid.UUID = Depends(get_active_org_id),
    db: AsyncSession = Depends(get_tenant_db),
) -> SummaryResponse:
    service = AIService(db)
    summary = await service.get_summary(summary_id, org_id)
    return SummaryResponse(
        id=summary.id,
        summary=summary.summary,
        action_items=summary.action_items or [],
        key_decisions=summary.key_decisions or [],
        participants=summary.participants or [],
        model=summary.model,
        tokens_in=summary.tokens_in,
        tokens_out=summary.tokens_out,
        cost_usd=summary.cost_usd,
        created_at=summary.created_at,
    )