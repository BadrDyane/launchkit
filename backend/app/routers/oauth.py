# launchkit/backend/app/routers/oauth.py
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.oauth_service import (
    build_google_auth_url,
    exchange_code_for_tokens,
    generate_oauth_state,
    get_google_user_info,
    upsert_google_user,
    validate_oauth_state,
)
from app.config import settings

router = APIRouter(prefix="/auth", tags=["oauth"])


@router.get("/google")
async def google_login(
    redirect_to: str = Query(default="/dashboard"),
) -> RedirectResponse:
    """Initiates Google OAuth flow. Redirects to Google consent screen."""
    state = generate_oauth_state(redirect_to)
    url = build_google_auth_url(state)
    return RedirectResponse(url=url)


@router.get("/google/callback")
async def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Google redirects here after user consents.
    Exchanges code → tokens → user info → upserts user.
    Redirects to frontend with access token in URL fragment.
    """
    try:
        redirect_to = validate_oauth_state(state)
        google_tokens = await exchange_code_for_tokens(code)
        user_info = await get_google_user_info(google_tokens["access_token"])

        user, access_token, raw_refresh = await upsert_google_user(
            db=db,
            google_id=user_info["sub"],
            email=user_info["email"],
            display_name=user_info.get("name"),
            avatar_url=user_info.get("picture"),
        )

        # Redirect to frontend — access token in fragment (never hits server logs)
        frontend_url = (
            f"{settings.FRONTEND_URL}/auth/callback"
            f"#access_token={access_token}"
            f"&redirect_to={redirect_to}"
        )
        return RedirectResponse(url=frontend_url)

    except Exception:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?error=oauth_failed"
        )