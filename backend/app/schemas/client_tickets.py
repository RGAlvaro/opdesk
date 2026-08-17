"""Pydantic contracts for restricted clients, tickets, and ticket comments."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.project import (
    TaskPriority,
    TaskStatus,
    TaskType,
    TicketAssignmentRequestStatus,
)
from app.schemas.projects import ProjectRead
from app.schemas.users import UserRead


class ProjectClientCreateRequest(BaseModel):
    """Request body for creating or granting a restricted project client."""

    email: str
    full_name: str
    password: str | None = None


class ProjectClientRead(BaseModel):
    """Client access row with safe client account details."""

    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    client_user_id: uuid.UUID
    granted_by_id: uuid.UUID
    revoked_at: datetime | None
    client: UserRead
    created_at: datetime


class ProjectClientListResponse(BaseModel):
    """Paginated client access collection for project settings."""

    items: list[ProjectClientRead]
    total: int
    limit: int
    offset: int


class TicketCreateRequest(BaseModel):
    """Client request body for creating a ticket."""

    subject: str
    description: str
    priority: str | None = None


class TicketUpdateRequest(BaseModel):
    """Internal request body for updating ticket task fields."""

    status: str | None = None
    priority: str | None = None
    assignee_id: uuid.UUID | None = None


class TicketRead(BaseModel):
    """Ticket representation shared by internal and client surfaces."""

    id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    assignee_id: uuid.UUID | None
    client_user_id: uuid.UUID | None
    task_type: TaskType
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketListResponse(BaseModel):
    """Paginated ticket collection."""

    items: list[TicketRead]
    total: int
    limit: int
    offset: int


class TicketCommentCreateRequest(BaseModel):
    """Request body for adding feedback to a ticket conversation."""

    body: str


class TicketCommentRead(BaseModel):
    """Public ticket comment shape with author attribution."""

    id: uuid.UUID
    task_id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    author_user_id: uuid.UUID
    body: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketCommentListResponse(BaseModel):
    """Paginated ticket comment thread."""

    items: list[TicketCommentRead]
    total: int
    limit: int
    offset: int


class TicketAssignmentRequestCreateRequest(BaseModel):
    """Request body for asking another project member to take a ticket."""

    target_user_id: uuid.UUID


class TicketAssignmentRequestRead(BaseModel):
    """Public assignment-request shape for the target worker."""

    id: uuid.UUID
    task_id: uuid.UUID
    organization_id: uuid.UUID
    project_id: uuid.UUID
    requested_by_id: uuid.UUID
    target_user_id: uuid.UUID
    status: TicketAssignmentRequestStatus
    ticket: TicketRead
    created_at: datetime
    responded_at: datetime | None


class TicketAssignmentRequestListResponse(BaseModel):
    """Paginated pending assignment requests for the current worker."""

    items: list[TicketAssignmentRequestRead]
    total: int
    limit: int
    offset: int


class ClientProjectListResponse(BaseModel):
    """Client-facing list of accessible projects."""

    items: list[ProjectRead]
