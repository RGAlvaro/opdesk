"""Pydantic contracts for organization and membership API operations."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.organization import MembershipRole


class OrganizationCreateRequest(BaseModel):
    """Request fields accepted when creating a tenant workspace."""

    name: str
    slug: str | None = None


class OrganizationUpdateRequest(BaseModel):
    """Optional organization fields an owner may update."""

    name: str | None = None
    slug: str | None = None


class OrganizationRead(BaseModel):
    """Organization representation enriched with the current user's role."""

    id: uuid.UUID
    name: str
    slug: str
    role: MembershipRole
    created_at: datetime
    updated_at: datetime


class OrganizationListResponse(BaseModel):
    """Paginated organizations visible to the authenticated user."""

    items: list[OrganizationRead]
    total: int
    limit: int
    offset: int


class MembershipRoleUpdateRequest(BaseModel):
    """Role replacement requested by an organization owner."""

    role: MembershipRole


class OwnershipTransferRequest(BaseModel):
    """Target member selected to become the organization's sole owner."""

    new_owner_user_id: uuid.UUID


class MembershipUserRead(BaseModel):
    """Safe user fields embedded in organization membership responses."""

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class MembershipRead(BaseModel):
    """Membership details returned without credentials or global privilege flags."""

    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: MembershipRole
    user: MembershipUserRead
    created_at: datetime
    updated_at: datetime


class MembershipListResponse(BaseModel):
    """Paginated membership list available to organization administrators."""

    items: list[MembershipRead]
    total: int
    limit: int
    offset: int
