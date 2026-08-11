"""Pydantic contracts for project API operations."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel

from app.models.project import ProjectStatus, ProjectVisibility


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
