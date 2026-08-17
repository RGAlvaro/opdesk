"""HTTP endpoints for task creation, filtering, and updates."""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Task, TaskLabel
from app.models.user import User
from app.schemas.labels import TaskLabelRead
from app.schemas.tasks import TaskCreateRequest, TaskListResponse, TaskRead, TaskUpdateRequest
from app.services.labels import TaskLabelService
from app.services.tasks import TaskService

router = APIRouter(prefix="/api/v1", tags=["tasks"])


def task_read(
    task: Task,
    watcher_ids: list[uuid.UUID] | None = None,
    labels: list[TaskLabelRead] | None = None,
) -> TaskRead:
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
        client_user_id=task.client_user_id,
        due_date=task.due_date,
        completed_at=task.completed_at,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        sort_order=task.sort_order,
        blocked_reason=task.blocked_reason,
        external_reference=task.external_reference,
        task_type=task.task_type,
        watcher_ids=watcher_ids or [],
        labels=labels or [],
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
        estimated_hours=payload.estimated_hours,
        actual_hours=payload.actual_hours,
        sort_order=payload.sort_order,
        blocked_reason=payload.blocked_reason,
        external_reference=payload.external_reference,
        task_type=payload.task_type,
        watcher_ids=payload.watcher_ids,
    )
    service = TaskService(db)
    label_service = TaskLabelService(db)
    return task_read(
        task,
        service.list_watcher_user_ids(task.id),
        [task_label_read(label) for label in label_service.list_task_labels(task.id)],
    )


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
    task_type: str | None = None,
    watcher_id: uuid.UUID | None = None,
    external_reference: str | None = None,
    label_id: uuid.UUID | None = None,
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
        task_type=task_type,
        watcher_id=watcher_id,
        external_reference=external_reference,
        label_id=label_id,
    )
    service = TaskService(db)
    label_service = TaskLabelService(db)
    labels_by_task = label_service.list_labels_for_tasks([task.id for task in tasks])
    return TaskListResponse(
        items=[
            task_read(
                task,
                service.list_watcher_user_ids(task.id),
                [task_label_read(label) for label in labels_by_task.get(task.id, [])],
            )
            for task in tasks
        ],
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
    service = TaskService(db)
    task, _ = service.get_task(current_user, task_id)
    label_service = TaskLabelService(db)
    return task_read(
        task,
        service.list_watcher_user_ids(task.id),
        [task_label_read(label) for label in label_service.list_task_labels(task.id)],
    )


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
        estimated_hours=payload.estimated_hours,
        actual_hours=payload.actual_hours,
        sort_order=payload.sort_order,
        blocked_reason=payload.blocked_reason,
        external_reference=payload.external_reference,
        task_type=payload.task_type,
        watcher_ids=payload.watcher_ids,
        fields_set=payload.model_fields_set,
    )
    service = TaskService(db)
    label_service = TaskLabelService(db)
    return task_read(
        task,
        service.list_watcher_user_ids(task.id),
        [task_label_read(label) for label in label_service.list_task_labels(task.id)],
    )


def task_label_read(label: TaskLabel) -> TaskLabelRead:
    """Convert a task label model into the public nested task contract."""
    return TaskLabelRead(
        id=label.id,
        organization_id=label.organization_id,
        project_id=label.project_id,
        name=label.name,
        color=label.color,
        description=label.description,
        created_by_id=label.created_by_id,
        archived_at=label.archived_at,
        created_at=label.created_at,
        updated_at=label.updated_at,
    )
