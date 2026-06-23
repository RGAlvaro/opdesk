"""HTTP endpoints for task creation, filtering, and updates."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Task
from app.models.user import User
from app.schemas.tasks import TaskCreateRequest, TaskListResponse, TaskRead, TaskUpdateRequest
from app.services.tasks import TaskService

router = APIRouter(prefix="/api/v1", tags=["tasks"])


def task_read(task: Task) -> TaskRead:
    """Convert a persisted task into the public response contract."""
    return TaskRead(
        id=task.id,
        organization_id=task.organization_id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        assignee_id=task.assignee_id,
        due_date=task.due_date,
        completed_at=task.completed_at,
        created_by_id=task.created_by_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("/projects/{project_id}/tasks", response_model=TaskRead, status_code=201)
def create_task(
    project_id: uuid.UUID,
    payload: TaskCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskRead:
    """Create a task in a non-archived project visible to the actor."""
    task = TaskService(db).create_task(
        current_user,
        project_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        due_date=payload.due_date,
    )
    return task_read(task)


@router.get("/projects/{project_id}/tasks", response_model=TaskListResponse)
def list_tasks(
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: str | None = None,
    assignee_id: uuid.UUID | None = None,
    priority: str | None = None,
    due_before: date | None = None,
    due_after: date | None = None,
) -> TaskListResponse:
    """List project tasks using pagination and optional filters."""
    tasks, total = TaskService(db).list_tasks(
        current_user,
        project_id,
        limit=limit,
        offset=offset,
        status=status,
        assignee_id=assignee_id,
        priority=priority,
        due_before=due_before,
        due_after=due_after,
    )
    return TaskListResponse(
        items=[task_read(task) for task in tasks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/tasks/{task_id}", response_model=TaskRead)
def get_task(
    task_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskRead:
    """Return one task only when the actor belongs to its organization."""
    task, _ = TaskService(db).get_task(current_user, task_id)
    return task_read(task)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskRead:
    """Update a task according to role and assignment policy."""
    task = TaskService(db).update_task(
        current_user,
        task_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        due_date=payload.due_date,
        fields_set=payload.model_fields_set,
    )
    return task_read(task)
