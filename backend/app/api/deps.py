from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.users import UserRepository
from app.services.security import decode_token


def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    access_token = request.cookies.get(settings.access_token_cookie_name)
    if access_token is None:
        raise APIError(401, "not_authenticated", "Authentication is required.")

    user_id = decode_token(access_token, "access", settings)
    if user_id is None:
        raise APIError(401, "not_authenticated", "Authentication is required.")

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise APIError(401, "not_authenticated", "Authentication is required.")
    return user
