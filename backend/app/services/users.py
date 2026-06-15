from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.user import User
from app.repositories.users import UserRepository
from app.services.security import hash_password, verify_password


@dataclass(frozen=True)
class AuthTokens:
    access_token: str
    refresh_token: str


def normalize_email(email: str) -> str:
    return email.strip().lower()


def normalize_full_name(full_name: str) -> str:
    return " ".join(full_name.strip().split())


def validate_password_policy(password: str) -> None:
    has_letter = any(character.isalpha() for character in password)
    has_number = any(character.isdigit() for character in password)
    if len(password) < 10 or not has_letter or not has_number:
        raise APIError(400, "weak_password", "Password does not meet policy requirements.")


def validate_full_name(full_name: str) -> str:
    normalized = normalize_full_name(full_name)
    if not normalized or len(normalized) > 120:
        raise APIError(400, "invalid_profile", "Full name must be between 1 and 120 characters.")
    return normalized


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)

    def register_user(self, email: str, password: str, full_name: str) -> User:
        normalized_email = normalize_email(email)
        normalized_name = validate_full_name(full_name)
        validate_password_policy(password)

        if self.users.get_by_email(normalized_email) is not None:
            raise APIError(409, "email_already_registered", "Email is already registered.")

        user = User(
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=normalized_name,
            is_superuser=self.users.count_users() == 0,
        )
        try:
            user = self.users.add(user)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise APIError(409, "email_already_registered", "Email is already registered.") from exc
        return user

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.users.get_by_email(normalize_email(email))
        if user is None or not verify_password(password, user.password_hash):
            raise APIError(401, "invalid_credentials", "Invalid email or password.")
        if not user.is_active:
            raise APIError(403, "inactive_user", "User is inactive.")
        return user

    def update_profile(self, user: User, full_name: str) -> User:
        user.full_name = validate_full_name(full_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
