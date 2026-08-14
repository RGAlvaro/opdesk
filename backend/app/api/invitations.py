"""HTTP endpoints for organization and project invitations."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.organization import Invitation
from app.models.user import User
from app.schemas.invitations import (
    InvitationListResponse,
    InvitationRead,
    OrganizationInvitationCreateRequest,
    ProjectInvitationCreateRequest,
)
from app.services.invitations import InvitationService

router = APIRouter(prefix="/api/v1", tags=["invitations"])


def invitation_read(service: InvitationService, invitation: Invitation) -> InvitationRead:
    """Convert an invitation model into a public response with safe display names."""
    invitation, organization, project = service.enrich_invitation(invitation)
    return InvitationRead(
        id=invitation.id,
        organization_id=invitation.organization_id,
        organization_name=organization.name if organization is not None else None,
        target_email=invitation.target_email,
        target_user_id=invitation.target_user_id,
        role=invitation.role,
        scope_type=invitation.scope_type,
        project_id=invitation.project_id,
        project_name=project.name if project is not None else None,
        status=invitation.status,
        accepted_at=invitation.accepted_at,
        declined_at=invitation.declined_at,
        cancelled_at=invitation.cancelled_at,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at,
    )


@router.post(
    "/organizations/{organization_id}/invitations",
    response_model=InvitationRead,
    status_code=201,
)
def create_organization_invitation(
    organization_id: uuid.UUID,
    payload: OrganizationInvitationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationRead:
    """Create a pending organization invitation for an existing user."""
    service = InvitationService(db)
    invitation = service.create_organization_invitation(
        current_user, organization_id, email=payload.email, role=payload.role
    )
    return invitation_read(service, invitation)


@router.get("/organizations/{organization_id}/invitations", response_model=InvitationListResponse)
def list_organization_invitations(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: str | None = None,
) -> InvitationListResponse:
    """List organization-owned invitations for owners and admins."""
    service = InvitationService(db)
    invitations, total = service.list_organization_invitations(
        current_user, organization_id, limit, offset, status
    )
    return InvitationListResponse(
        items=[invitation_read(service, invitation) for invitation in invitations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/organizations/{organization_id}/invitations/{invitation_id}", status_code=204)
def cancel_invitation(
    organization_id: uuid.UUID,
    invitation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Cancel a pending organization or project invitation in the organization."""
    InvitationService(db).cancel_invitation(current_user, organization_id, invitation_id)
    return Response(status_code=204)


@router.get("/invitations", response_model=InvitationListResponse)
def list_my_invitations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    status: str | None = None,
) -> InvitationListResponse:
    """List invitations addressed to the current user."""
    service = InvitationService(db)
    invitations, total = service.list_my_invitations(current_user, limit, offset, status)
    return InvitationListResponse(
        items=[invitation_read(service, invitation) for invitation in invitations],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/invitations/{invitation_id}/accept", response_model=InvitationRead)
def accept_invitation(
    invitation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationRead:
    """Accept a pending invitation addressed to the current user."""
    service = InvitationService(db)
    invitation = service.accept_invitation(current_user, invitation_id)
    return invitation_read(service, invitation)


@router.post("/invitations/{invitation_id}/decline", response_model=InvitationRead)
def decline_invitation(
    invitation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationRead:
    """Decline a pending invitation addressed to the current user."""
    service = InvitationService(db)
    invitation = service.decline_invitation(current_user, invitation_id)
    return invitation_read(service, invitation)


@router.post("/projects/{project_id}/invitations", response_model=InvitationRead, status_code=201)
def create_project_invitation(
    project_id: uuid.UUID,
    payload: ProjectInvitationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> InvitationRead:
    """Create a pending project invitation for an existing organization member."""
    service = InvitationService(db)
    invitation = service.create_project_invitation(
        current_user, project_id, user_id=payload.user_id
    )
    return invitation_read(service, invitation)
