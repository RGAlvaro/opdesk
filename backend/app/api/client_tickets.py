"""HTTP endpoints for restricted clients, project tickets, and ticket comments."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.projects import project_read
from app.db.session import get_db
from app.models.project import ProjectClientAccess, Task, TicketAssignmentRequest, TicketComment
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.client_tickets import (
    ClientProjectListResponse,
    ProjectClientCreateRequest,
    ProjectClientListResponse,
    ProjectClientRead,
    TicketAssignmentRequestCreateRequest,
    TicketAssignmentRequestListResponse,
    TicketAssignmentRequestRead,
    TicketCommentCreateRequest,
    TicketCommentListResponse,
    TicketCommentRead,
    TicketCreateRequest,
    TicketListResponse,
    TicketRead,
    TicketUpdateRequest,
)
from app.schemas.users import UserRead
from app.services.client_tickets import ClientTicketService

router = APIRouter(prefix="/api/v1", tags=["client-tickets"])


def ticket_read(ticket: Task) -> TicketRead:
    """Convert a ticket task into the shared ticket response contract."""
    return TicketRead.model_validate(ticket)


def ticket_comment_read(comment: TicketComment) -> TicketCommentRead:
    """Convert a persisted ticket comment into the public response contract."""
    return TicketCommentRead.model_validate(comment)


def ticket_assignment_request_read(
    db: Session, request: TicketAssignmentRequest
) -> TicketAssignmentRequestRead:
    """Convert a handoff request into the target worker response contract."""
    ticket = db.get(Task, request.task_id)
    assert ticket is not None
    return TicketAssignmentRequestRead(
        id=request.id,
        task_id=request.task_id,
        organization_id=request.organization_id,
        project_id=request.project_id,
        requested_by_id=request.requested_by_id,
        target_user_id=request.target_user_id,
        status=request.status,
        ticket=ticket_read(ticket),
        created_at=request.created_at,
        responded_at=request.responded_at,
    )


def project_client_read(
    access: ProjectClientAccess, client_user: User | None
) -> ProjectClientRead | None:
    """Convert a client access row into a response when its user still exists."""
    if client_user is None:
        return None
    return ProjectClientRead(
        id=access.id,
        organization_id=access.organization_id,
        project_id=access.project_id,
        client_user_id=access.client_user_id,
        granted_by_id=access.granted_by_id,
        revoked_at=access.revoked_at,
        client=UserRead.model_validate(client_user),
        created_at=access.created_at,
    )


@router.get("/projects/{project_id}/clients", response_model=ProjectClientListResponse)
def list_project_clients(
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectClientListResponse:
    """List restricted client accounts with access to one project."""
    rows, total = ClientTicketService(db).list_project_clients(
        current_user, project_id, limit, offset
    )
    items = [
        item
        for item in (project_client_read(access, client_user) for access, client_user in rows)
        if item is not None
    ]
    return ProjectClientListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post("/projects/{project_id}/clients", response_model=ProjectClientRead, status_code=201)
def create_project_client(
    project_id: uuid.UUID,
    payload: ProjectClientCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ProjectClientRead:
    """Create or grant a restricted client account for a project."""
    access = ClientTicketService(db).create_or_grant_project_client(
        current_user,
        project_id,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
    )
    client_user = UserRepository(db).get_by_id(access.client_user_id)
    response = project_client_read(access, client_user)
    assert response is not None
    return response


@router.delete("/projects/{project_id}/clients/{client_access_id}", status_code=204)
def revoke_project_client(
    project_id: uuid.UUID,
    client_access_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Revoke one restricted client's future access to a project."""
    ClientTicketService(db).revoke_project_client(current_user, project_id, client_access_id)
    return Response(status_code=204)


@router.get("/projects/{project_id}/tickets", response_model=TicketListResponse)
def list_project_tickets(
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TicketListResponse:
    """List client tickets visible to internal project members."""
    tickets, total = ClientTicketService(db).list_project_tickets(
        current_user, project_id, limit, offset
    )
    return TicketListResponse(
        items=[ticket_read(ticket) for ticket in tickets], total=total, limit=limit, offset=offset
    )


@router.get("/tickets/{ticket_id}", response_model=TicketRead)
def get_ticket(
    ticket_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketRead:
    """Return one ticket to an internal project member."""
    return ticket_read(ClientTicketService(db).get_internal_ticket(current_user, ticket_id))


@router.patch("/tickets/{ticket_id}", response_model=TicketRead)
def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketRead:
    """Update owner/admin-managed ticket fields."""
    ticket = ClientTicketService(db).update_ticket(
        current_user,
        ticket_id,
        status=payload.status,
        priority=payload.priority,
        assignee_id=payload.assignee_id,
        fields_set=payload.model_fields_set,
    )
    return ticket_read(ticket)


@router.post(
    "/tickets/{ticket_id}/assignment-requests",
    response_model=TicketAssignmentRequestRead,
    status_code=201,
)
def create_ticket_assignment_request(
    ticket_id: uuid.UUID,
    payload: TicketAssignmentRequestCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketAssignmentRequestRead:
    """Ask another eligible project member to accept a ticket assignment."""
    request = ClientTicketService(db).create_assignment_request(
        current_user, ticket_id, payload.target_user_id
    )
    return ticket_assignment_request_read(db, request)


@router.get("/ticket-assignment-requests", response_model=TicketAssignmentRequestListResponse)
def list_ticket_assignment_requests(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TicketAssignmentRequestListResponse:
    """List pending ticket assignment requests addressed to the current user."""
    requests, total = ClientTicketService(db).list_assignment_requests(current_user, limit, offset)
    return TicketAssignmentRequestListResponse(
        items=[ticket_assignment_request_read(db, request) for request in requests],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/ticket-assignment-requests/{request_id}/accept",
    response_model=TicketAssignmentRequestRead,
)
def accept_ticket_assignment_request(
    request_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketAssignmentRequestRead:
    """Accept a pending ticket handoff and become the assignee."""
    request = ClientTicketService(db).accept_assignment_request(current_user, request_id)
    return ticket_assignment_request_read(db, request)


@router.post(
    "/ticket-assignment-requests/{request_id}/decline",
    response_model=TicketAssignmentRequestRead,
)
def decline_ticket_assignment_request(
    request_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketAssignmentRequestRead:
    """Decline a pending ticket handoff without changing assignment."""
    request = ClientTicketService(db).decline_assignment_request(current_user, request_id)
    return ticket_assignment_request_read(db, request)


@router.get("/tickets/{ticket_id}/comments", response_model=TicketCommentListResponse)
def list_ticket_comments(
    ticket_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TicketCommentListResponse:
    """List ticket comments for an internal conversation participant."""
    comments, total = ClientTicketService(db).list_comments(current_user, ticket_id, limit, offset)
    return TicketCommentListResponse(
        items=[ticket_comment_read(comment) for comment in comments],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/tickets/{ticket_id}/comments", response_model=TicketCommentRead, status_code=201)
def add_ticket_comment(
    ticket_id: uuid.UUID,
    payload: TicketCommentCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketCommentRead:
    """Add internal feedback to a ticket conversation."""
    comment = ClientTicketService(db).add_comment(current_user, ticket_id, payload.body)
    return ticket_comment_read(comment)


@router.get("/client/projects", response_model=ClientProjectListResponse)
def list_client_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ClientProjectListResponse:
    """List projects available to the restricted client account."""
    projects = ClientTicketService(db).list_client_projects(current_user)
    return ClientProjectListResponse(items=[project_read(project) for project in projects])


@router.post("/client/projects/{project_id}/tickets", response_model=TicketRead, status_code=201)
def create_client_ticket(
    project_id: uuid.UUID,
    payload: TicketCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketRead:
    """Create a ticket in a project where the client has active access."""
    ticket = ClientTicketService(db).create_client_ticket(
        current_user,
        project_id,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
    )
    return ticket_read(ticket)


@router.get("/client/tickets", response_model=TicketListResponse)
def list_client_tickets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TicketListResponse:
    """List tickets created by the restricted client account."""
    tickets, total = ClientTicketService(db).list_client_tickets(current_user, limit, offset)
    return TicketListResponse(
        items=[ticket_read(ticket) for ticket in tickets], total=total, limit=limit, offset=offset
    )


@router.get("/client/tickets/{ticket_id}", response_model=TicketRead)
def get_client_ticket(
    ticket_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketRead:
    """Return one client-owned ticket."""
    return ticket_read(ClientTicketService(db).get_client_ticket(current_user, ticket_id))


@router.get("/client/tickets/{ticket_id}/comments", response_model=TicketCommentListResponse)
def list_client_ticket_comments(
    ticket_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TicketCommentListResponse:
    """List comments for a client-owned ticket."""
    comments, total = ClientTicketService(db).list_comments(current_user, ticket_id, limit, offset)
    return TicketCommentListResponse(
        items=[ticket_comment_read(comment) for comment in comments],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/client/tickets/{ticket_id}/comments", response_model=TicketCommentRead, status_code=201
)
def add_client_ticket_comment(
    ticket_id: uuid.UUID,
    payload: TicketCommentCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> TicketCommentRead:
    """Add client feedback to a client-owned ticket."""
    comment = ClientTicketService(db).add_comment(current_user, ticket_id, payload.body)
    return ticket_comment_read(comment)
