"""HTTP endpoints for project management inside organizations."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.projects import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectRead,
    ProjectUpdateRequest,
)
from app.services.projects import ProjectService

router = APIRouter(prefix="/api/v1", tags=["projects"])


def project_read(project: Project) -> ProjectRead:
    """Convert a persisted project into the public response contract."""
    return ProjectRead(
        id=project.id,
        organization_id=project.organization_id,
        name=project.name,
        description=project.description,
        is_archived=project.is_archived,
        status=project.status,
        start_date=project.start_date,
        end_date=project.end_date,
        budget_amount=project.budget_amount,
        budget_currency=project.budget_currency,
        visibility=project.visibility,
        project_owner_id=project.project_owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post(
    "/organizations/{organization_id}/projects", response_model=ProjectRead, status_code=201
)
def create_project(
    organization_id: uuid.UUID,
    payload: ProjectCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    """Create a project when the actor can manage the organization."""
    project = ProjectService(db).create_project(
        current_user,
        organization_id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        budget_amount=payload.budget_amount,
        budget_currency=payload.budget_currency,
        visibility=payload.visibility,
        project_owner_id=payload.project_owner_id,
    )
    return project_read(project)


@router.get("/organizations/{organization_id}/projects", response_model=ProjectListResponse)
def list_projects(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectListResponse:
    """List projects for organization members with standard pagination."""
    projects, total = ProjectService(db).list_projects(current_user, organization_id, limit, offset)
    return ProjectListResponse(
        items=[project_read(project) for project in projects],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/projects/{project_id}", response_model=ProjectRead)
def get_project(
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    """Return one project only when the actor belongs to its organization."""
    project, _ = ProjectService(db).get_project(current_user, project_id)
    return project_read(project)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectRead:
    """Update project metadata or archive state for owners and admins."""
    project = ProjectService(db).update_project(
        current_user,
        project_id,
        name=payload.name,
        description=payload.description,
        is_archived=payload.is_archived,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        budget_amount=payload.budget_amount,
        budget_currency=payload.budget_currency,
        visibility=payload.visibility,
        project_owner_id=payload.project_owner_id,
        fields_set=payload.model_fields_set,
    )
    return project_read(project)
