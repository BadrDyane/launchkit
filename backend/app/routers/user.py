# launchkit/backend/app/routers/user.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.user import (
    ChangePasswordRequest,
    EmailVerifyRequest,
    PasswordResetConfirm,
    PasswordResetRequestBody,
)
from app.schemas.auth import UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/user", tags=["user"])


@router.post("/send-verification-email", response_model=MessageResponse)
async def send_verification(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    service = UserService(db)
    await service.send_verification_email(current_user)
    return MessageResponse(message="Verification email sent")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    body: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = UserService(db)
    await service.verify_email(body.token)
    return MessageResponse(message="Email verified successfully")


@router.post("/request-password-reset", response_model=MessageResponse)
async def request_password_reset(
    body: PasswordResetRequestBody,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = UserService(db)
    await service.request_password_reset(body.email)
    # Always 200 — prevents user enumeration
    return MessageResponse(message="If that email exists, a reset link has been sent")


@router.post("/confirm-password-reset", response_model=MessageResponse)
async def confirm_password_reset(
    body: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    service = UserService(db)
    await service.confirm_password_reset(body.token, body.new_password)
    return MessageResponse(message="Password reset successfully")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    service = UserService(db)
    await service.change_password(
        current_user,
        body.current_password,
        body.new_password,
    )
    return MessageResponse(message="Password changed successfully")


@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)