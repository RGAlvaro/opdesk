"""HTTP endpoints for project labels and task label assignment."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.tasks import task_read
from app.db.session import get_db
from app.models.project import TaskLabel
from app.models.user import User
from app.schemas.labels import (
    TaskLabelAssignRequest,
    TaskLabelCreateRequest,
    TaskLabelListResponse,
    TaskLabelRead,
    TaskLabelUpdateRequest,
)
from app.schemas.tasks import TaskRead
from app.services.labels import TaskLabelService
from app.services.tasks import TaskService

router = APIRouter(prefix="/api/v1", tags=["task-labels"])


def task_label_read(label: TaskLabel) -> TaskLabelRead:
    """Convert a persisted label into the public response contract."""
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


@router.get("/projects/{project_id}/labels", response_model=TaskLabelListResponse)
def list_project_labels(
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    include_archived: bool = False,
) -> TaskLabelListResponse:
    """List labels for a project visible to the actor."""
    labels, total = TaskLabelService(db).list_labels(
        current_user,
        project_id,
        limit=limit,
        offset=offset,
        include_archived=include_archived,
    )
    return TaskLabelListResponse(
        items=[task_label_read(label) for label in labels],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/projects/{project_id}/labels", response_model=TaskLabelRead, status_code=201)
def create_project_label(
    project_id: uuid.UUID,
    payload: TaskLabelCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskLabelRead:
    """Create a label for a project visible to the actor."""
    label = TaskLabelService(db).create_label(
        current_user,
        project_id,
        name=payload.name,
        color=payload.color,
        description=payload.description,
    )
    return task_label_read(label)


@router.patch("/projects/{project_id}/labels/{label_id}", response_model=TaskLabelRead)
def update_project_label(
    project_id: uuid.UUID,
    label_id: uuid.UUID,
    payload: TaskLabelUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskLabelRead:
    """Update label metadata or archive state for a project member."""
    label = TaskLabelService(db).update_label(
        current_user,
        project_id,
        label_id,
        name=payload.name,
        color=payload.color,
        description=payload.description,
        is_archived=payload.is_archived,
        fields_set=payload.model_fields_set,
    )
    return task_label_read(label)


@router.post("/tasks/{task_id}/labels", response_model=TaskRead)
def apply_task_label(
    task_id: uuid.UUID,
    payload: TaskLabelAssignRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TaskRead:
    """Apply one active project label to a task the actor may update."""
    label_service = TaskLabelService(db)
    task = label_service.apply_label(current_user, task_id, payload.label_id)
    task_service = TaskService(db)
    return task_read(
        task,
        task_service.list_watcher_user_ids(task.id),
        [task_label_read(label) for label in label_service.list_task_labels(task.id)],
    )


@router.delete("/tasks/{task_id}/labels/{label_id}", status_code=204)
def remove_task_label(
    task_id: uuid.UUID,
    label_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Remove one label from a task the actor may update."""
    TaskLabelService(db).remove_label(current_user, task_id, label_id)
    return Response(status_code=204)
