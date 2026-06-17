"""Authentication endpoints for registration, login, token refresh, and logout."""

import uuid
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.repositories.users import UserRepository
from app.schemas.users import LoginRequest, LoginResponse, RegisterRequest, StatusResponse, UserRead
from app.services.security import create_token, decode_token
from app.services.users import UserService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def set_auth_cookies(response: Response, user_id: uuid.UUID, settings: Settings) -> None:
    """Issue browser cookies for a freshly authenticated user session."""
    access_token = create_token(
        user_id=user_id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        settings=settings,
    )
    refresh_token = create_token(
        user_id=user_id,
        token_type="refresh",
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        settings=settings,
    )
    response.set_cookie(
        settings.access_token_cookie_name,
        access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )
    response.set_cookie(
        settings.refresh_token_cookie_name,
        refresh_token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: RegisterRequest, db: Annotated[Session, Depends(get_db)]) -> UserRead:
    """Create a user account and return the safe public profile."""
    user = UserService(db).register_user(payload.email, payload.password, payload.full_name)
    return UserRead.model_validate(user)


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> LoginResponse:
    """Authenticate credentials, set auth cookies, and return the logged-in user."""
    user = UserService(db).authenticate_user(payload.email, payload.password)
    set_auth_cookies(response, user.id, settings)
    return LoginResponse(user=UserRead.model_validate(user))


@router.post("/refresh", response_model=StatusResponse)
def refresh(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> StatusResponse:
    """Validate the refresh cookie and replace the short-lived access cookie."""
    refresh_token = request.cookies.get(settings.refresh_token_cookie_name)
    if refresh_token is None:
        raise APIError(401, "invalid_refresh_token", "Refresh token is invalid.")

    user_id = decode_token(refresh_token, "refresh", settings)
    if user_id is None:
        raise APIError(401, "invalid_refresh_token", "Refresh token is invalid.")

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise APIError(401, "invalid_refresh_token", "Refresh token is invalid.")

    access_token = create_token(
        user_id=user.id,
        token_type="access",
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        settings=settings,
    )
    response.set_cookie(
        settings.access_token_cookie_name,
        access_token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )
    return StatusResponse(status="ok")


@router.post("/logout", status_code=204)
def logout(response: Response, settings: Annotated[Settings, Depends(get_settings)]) -> Response:
    """Clear auth cookies so the browser session is no longer authenticated."""
    response.delete_cookie(settings.access_token_cookie_name)
    response.delete_cookie(settings.refresh_token_cookie_name)
    response.status_code = 204
    return response
