"""Current-user profile endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.users import UserRead, UserUpdateRequest
from app.services.users import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    """Return the authenticated user's public profile."""
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: UserUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> UserRead:
    """Update mutable fields on the authenticated user's own profile."""
    user = UserService(db).update_profile(
        current_user,
        full_name=payload.full_name,
        email=payload.email,
        current_password=payload.current_password,
        job_title=payload.job_title,
        phone=payload.phone,
        timezone=payload.timezone,
        locale=payload.locale,
        avatar_url=payload.avatar_url,
        bio=payload.bio,
        fields_set=payload.model_fields_set,
    )
    return UserRead.model_validate(user)
