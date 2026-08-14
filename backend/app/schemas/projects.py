"""Pydantic contracts for project API operations."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.organization import MembershipRole
from app.models.project import ProjectStatus, ProjectVisibility
from app.schemas.organizations import MembershipUserRead


class ProjectCreateRequest(BaseModel):
    """Request fields accepted when creating a project."""

    name: str
    description: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_amount: Decimal | None = None
    budget_currency: str | None = None
    visibility: str | None = None
    project_owner_id: uuid.UUID | None = None


class ProjectUpdateRequest(BaseModel):
    """Optional project fields an owner or admin may update."""

    name: str | None = None
    description: str | None = None
    is_archived: bool | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget_amount: Decimal | None = None
    budget_currency: str | None = None
    visibility: str | None = None
    project_owner_id: uuid.UUID | None = None


class ProjectRead(BaseModel):
    """Public project representation for organization members."""

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    is_archived: bool
    status: ProjectStatus
    start_date: date | None
    end_date: date | None
    budget_amount: Decimal | None
    budget_currency: str | None
    visibility: ProjectVisibility
    project_owner_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated projects visible to one organization member."""

    items: list[ProjectRead]
    total: int
    limit: int
    offset: int


class ProjectMembershipRead(BaseModel):
    """Explicit project participation returned to allowed project viewers."""

    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    user_id: uuid.UUID
    added_by_id: uuid.UUID | None
    role: MembershipRole
    user: MembershipUserRead
    created_at: datetime


class ProjectMembershipListResponse(BaseModel):
    """Paginated list of explicit project members."""

    items: list[ProjectMembershipRead]
    total: int
    limit: int
    offset: int
