"""Pydantic contracts for organization and project invitations."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.organization import InvitationScope, InvitationStatus, MembershipRole


class OrganizationInvitationCreateRequest(BaseModel):
    """Email and role requested for an organization invitation."""

    email: str
    role: MembershipRole


class ProjectInvitationCreateRequest(BaseModel):
    """Existing organization member requested for project access."""

    user_id: uuid.UUID


class InvitationRead(BaseModel):
    """Public invitation representation without hidden tenant data."""

    id: uuid.UUID
    organization_id: uuid.UUID
    organization_name: str | None = None
    target_email: str
    target_user_id: uuid.UUID
    role: MembershipRole | None
    scope_type: InvitationScope
    project_id: uuid.UUID | None
    project_name: str | None = None
    status: InvitationStatus
    accepted_at: datetime | None
    declined_at: datetime | None
    cancelled_at: datetime | None
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class InvitationListResponse(BaseModel):
    """Paginated invitation list for recipient or organization admins."""

    items: list[InvitationRead]
    total: int
    limit: int
    offset: int
