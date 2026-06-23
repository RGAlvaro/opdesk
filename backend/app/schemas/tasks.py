"""Pydantic contracts for task API operations."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models.project import TaskPriority, TaskStatus


class TaskCreateRequest(BaseModel):
    """Request fields accepted when creating a task."""

    title: str
    description: str | None = None
    priority: str | None = None
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None


class TaskUpdateRequest(BaseModel):
    """Optional task fields accepted for an update."""

    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None


class TaskRead(BaseModel):
    """Public task representation for organization members."""

    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: uuid.UUID | None
    due_date: date | None
    completed_at: datetime | None
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Paginated task collection for a project."""

    items: list[TaskRead]
    total: int
    limit: int
    offset: int
