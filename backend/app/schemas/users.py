"""Pydantic schemas for user, authentication, and profile API payloads."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserRead(BaseModel):
    """Public user representation returned by auth and profile endpoints."""

    id: uuid.UUID
    email: str
    full_name: str
    job_title: str | None
    phone: str | None
    timezone: str | None
    locale: str | None
    avatar_url: str | None
    bio: str | None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRequest(BaseModel):
    """Request body for updating the current user's profile."""

    full_name: str | None = None
    email: str | None = None
    current_password: str | None = None
    job_title: str | None = None
    phone: str | None = None
    timezone: str | None = None
    locale: str | None = None
    avatar_url: str | None = None
    bio: str | None = None


class RegisterRequest(BaseModel):
    """Request body for creating an account with email, password, and name."""

    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    """Request body for authenticating with email and password."""

    email: str
    password: str


class LoginResponse(BaseModel):
    """Successful login response containing the safe user profile."""

    user: UserRead


class StatusResponse(BaseModel):
    """Small status envelope for auth operations that only report success."""

    status: str
