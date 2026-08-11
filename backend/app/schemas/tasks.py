"""Pydantic contracts for task API operations."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.project import TaskPriority, TaskStatus, TaskType


class TaskCreateRequest(BaseModel):
    """Request fields accepted when creating a task."""

    title: str
    description: str | None = None
    priority: str | None = None
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None
    estimated_hours: Decimal | None = None
    actual_hours: Decimal | None = None
    sort_order: int | None = None
    blocked_reason: str | None = None
    external_reference: str | None = None
    task_type: str | None = None
    watcher_ids: list[uuid.UUID] | None = None


class TaskUpdateRequest(BaseModel):
    """Optional task fields accepted for an update."""

    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee_id: uuid.UUID | None = None
    due_date: date | None = None
    estimated_hours: Decimal | None = None
    actual_hours: Decimal | None = None
    sort_order: int | None = None
    blocked_reason: str | None = None
    external_reference: str | None = None
    task_type: str | None = None
    watcher_ids: list[uuid.UUID] | None = None


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
    estimated_hours: Decimal | None
    actual_hours: Decimal | None
    sort_order: int | None
    blocked_reason: str | None
    external_reference: str | None
    task_type: TaskType
    watcher_ids: list[uuid.UUID] = Field(default_factory=list)
    created_by_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Paginated task collection for a project."""

    items: list[TaskRead]
    total: int
    limit: int
    offset: int
