"""Password hashing and JWT helpers for browser authentication."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from app.core.config import Settings

password_hasher = PasswordHasher(time_cost=2, memory_cost=19_456, parallelism=1)


def hash_password(password: str) -> str:
    """Hash a plaintext password with the configured Argon2 parameters."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against an Argon2 hash without raising."""
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError):
        return False


def create_token(
    user_id: uuid.UUID, token_type: str, expires_delta: timedelta, settings: Settings
) -> str:
    """Create a signed JWT for the given user, token type, and lifetime."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.auth_secret_key, algorithm="HS256")


def decode_token(token: str, expected_type: str, settings: Settings) -> uuid.UUID | None:
    """Return the token subject when signature, expiry, and token type are valid."""
    try:
        payload = jwt.decode(token, settings.auth_secret_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None

    if payload.get("type") != expected_type:
        return None

    subject = payload.get("sub")
    if not isinstance(subject, str):
        return None

    try:
        return uuid.UUID(subject)
    except ValueError:
        return None
