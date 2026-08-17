"""User business rules for registration, authentication, and profile updates."""

import logging
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.user import User, UserAccountType
from app.repositories.users import UserRepository
from app.services.metadata import optional_locale, optional_string, optional_timezone, optional_url
from app.services.security import hash_password, verify_password

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthTokens:
    """Pair of auth token strings when service-level token transport is needed."""

    access_token: str
    refresh_token: str


def normalize_email(email: str) -> str:
    """Normalize email addresses before uniqueness checks and login lookups."""
    return email.strip().lower()


def normalize_full_name(full_name: str) -> str:
    """Collapse whitespace around profile names for stable storage and display."""
    return " ".join(full_name.strip().split())


def validate_password_policy(password: str) -> None:
    """Enforce the minimum password shape required by the auth spec."""
    has_letter = any(character.isalpha() for character in password)
    has_number = any(character.isdigit() for character in password)
    if len(password) < 10 or not has_letter or not has_number:
        raise APIError(400, "weak_password", "Password does not meet policy requirements.")


def validate_full_name(full_name: str) -> str:
    """Return a normalized profile name or raise the API validation error."""
    normalized = normalize_full_name(full_name)
    if not normalized or len(normalized) > 120:
        raise APIError(400, "invalid_profile", "Full name must be between 1 and 120 characters.")
    return normalized


class UserService:
    """Coordinate user business rules with repositories and transaction commits."""

    def __init__(self, db: Session) -> None:
        """Create service collaborators bound to the active database session."""
        self.db = db
        self.users = UserRepository(db)

    def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        *,
        account_type: UserAccountType = UserAccountType.INTERNAL,
    ) -> User:
        """Create a user account and promote the first account to superuser."""
        normalized_email = normalize_email(email)
        normalized_name = validate_full_name(full_name)
        validate_password_policy(password)

        if self.users.get_by_email(normalized_email) is not None:
            raise APIError(409, "email_already_registered", "Email is already registered.")

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=normalized_name,
            is_superuser=self.users.count_users() == 0 and account_type == UserAccountType.INTERNAL,
            account_type=account_type,
        )
        try:
            user = self.users.add(user)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise APIError(409, "email_already_registered", "Email is already registered.") from exc
        return user

    def authenticate_user(self, email: str, password: str) -> User:
        """Validate login credentials without leaking which field failed."""
        user = self.users.get_by_email(normalize_email(email))
        if user is None or not verify_password(password, user.password_hash):
            raise APIError(401, "invalid_credentials", "Invalid email or password.")
        if not user.is_active:
            raise APIError(403, "inactive_user", "User is inactive.")
        return user

    def update_profile(
        self,
        user: User,
        *,
        full_name: str | None,
        email: str | None,
        current_password: str | None,
        job_title: str | None,
        phone: str | None,
        timezone: str | None,
        locale: str | None,
        avatar_url: str | None,
        bio: str | None,
        fields_set: set[str],
    ) -> User:
        """Persist allowed profile metadata and password-confirmed email changes."""
        if not fields_set:
            raise APIError(400, "invalid_profile", "At least one field must be updated.")
        if "full_name" in fields_set:
            if full_name is None:
                raise APIError(400, "invalid_profile", "Full name is required.")
            user.full_name = validate_full_name(full_name)
        if "email" in fields_set:
            if email is None:
                raise APIError(400, "invalid_profile", "Email is required.")
            normalized_email = normalize_email(email)
            if normalized_email != user.email:
                if not current_password or not verify_password(
                    current_password, user.password_hash
                ):
                    raise APIError(
                        403,
                        "invalid_current_password",
                        "Current password confirmation failed.",
                    )
                existing = self.users.get_by_email(normalized_email)
                if existing is not None and existing.id != user.id:
                    raise APIError(
                        409,
                        "email_already_registered",
                        "Email is already registered.",
                    )
                previous_email = user.email
                user.email = normalized_email
                logger.info(
                    "user email changed actor_id=%s old_email=%s new_email=%s",
                    user.id,
                    previous_email,
                    normalized_email,
                )
        if "job_title" in fields_set:
            user.job_title = optional_string(
                job_title, max_length=120, code="invalid_profile", field="job_title"
            )
        if "phone" in fields_set:
            user.phone = optional_string(
                phone, max_length=40, code="invalid_profile", field="phone"
            )
        if "timezone" in fields_set:
            user.timezone = optional_timezone(timezone)
        if "locale" in fields_set:
            user.locale = optional_locale(locale)
        if "avatar_url" in fields_set:
            user.avatar_url = optional_url(avatar_url, code="invalid_profile", field="avatar_url")
        if "bio" in fields_set:
            user.bio = optional_string(bio, max_length=1000, code="invalid_profile", field="bio")
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
