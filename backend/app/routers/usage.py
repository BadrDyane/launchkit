# launchkit/backend/app/routers/usage.py
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.tenant import get_active_org_id, get_tenant_db
from app.schemas.usage import UsageSummaryResponse
from app.services.usage_service import UsageService

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/", response_model=UsageSummaryResponse)
async def get_usage(
    org_id: uuid.UUID = Depends(get_active_org_id),
    db: AsyncSession = Depends(get_tenant_db),
) -> UsageSummaryResponse:
    service = UsageService(db)
    usage = await service.get_current_usage(org_id)
    return UsageSummaryResponse(**usage)