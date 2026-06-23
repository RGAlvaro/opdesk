"""Pydantic contracts for project API operations."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class ProjectCreateRequest(BaseModel):
    """Request fields accepted when creating a project."""

    name: str
    description: str | None = None


class ProjectUpdateRequest(BaseModel):
    """Optional project fields an owner or admin may update."""

    name: str | None = None
    description: str | None = None
    is_archived: bool | None = None


class ProjectRead(BaseModel):
    """Public project representation for organization members."""

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated projects visible to one organization member."""

    items: list[ProjectRead]
    total: int
    limit: int
    offset: int
