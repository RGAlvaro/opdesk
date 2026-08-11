"""Pydantic contracts for project task labels and task assignments."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class TaskLabelCreateRequest(BaseModel):
    """Request fields accepted when creating a project label."""

    name: str
    color: str
    description: str | None = None


class TaskLabelUpdateRequest(BaseModel):
    """Optional label fields accepted for metadata or archive updates."""

    name: str | None = None
    color: str | None = None
    description: str | None = None
    is_archived: bool | None = None


class TaskLabelAssignRequest(BaseModel):
    """Request body for applying one existing label to a task."""

    label_id: uuid.UUID


class TaskLabelRead(BaseModel):
    """Public project label representation for visible project tasks."""

    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    color: str
    description: str | None
    created_by_id: uuid.UUID
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TaskLabelListResponse(BaseModel):
    """Paginated labels visible to one project member."""

    items: list[TaskLabelRead]
    total: int
    limit: int
    offset: int
