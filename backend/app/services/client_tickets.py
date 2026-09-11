"""Business rules for restricted project clients, tickets, and comments."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import (
    Project,
    ProjectClientAccess,
    Task,
    TaskPriority,
    TaskType,
    TicketAssignmentRequest,
    TicketAssignmentRequestStatus,
    TicketComment,
)
from app.models.user import User, UserAccountType
from app.repositories.client_tickets import ClientTicketRepository
from app.repositories.organizations import OrganizationRepository
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository
from app.services.notifications import NotificationService
from app.services.tasks import parse_task_priority, parse_task_status, validate_task_title
from app.services.users import UserService, normalize_email


def validate_ticket_body(body: str, *, code: str = "invalid_comment") -> str:
    """Normalize and validate user-generated ticket text."""
    normalized = body.strip()
    if not normalized or len(normalized) > 4000:
        raise APIError(400, code, "Text must be between 1 and 4000 characters.")
    return normalized


class ClientTicketService:
    """Coordinate client access, ticket persistence, and comment policy."""

    def __init__(self, db: Session) -> None:
        """Create collaborators bound to the active database session."""
        self.db = db
        self.client_tickets = ClientTicketRepository(db)
        self.organizations = OrganizationRepository(db)
        self.projects = ProjectRepository(db)
        self.tasks = TaskRepository(db)
        self.users = UserRepository(db)

    def create_or_grant_project_client(
        self,
        actor: User,
        project_id: uuid.UUID,
        *,
        email: str,
        full_name: str,
        password: str | None,
    ) -> ProjectClientAccess:
        """Create a restricted client account when needed and grant project access."""
        project, membership = self._get_project_for_internal_member(actor, project_id)
        self._require_owner_admin(membership)
        normalized_email = normalize_email(email)
        client_user = self.users.get_by_email(normalized_email)
        if client_user is None:
            if password is None:
                raise APIError(400, "invalid_client", "Password is required for new clients.")
            client_user = UserService(self.db).register_user(
                normalized_email,
                password,
                full_name,
                account_type=UserAccountType.CLIENT,
            )
        elif client_user.account_type != UserAccountType.CLIENT:
            raise APIError(409, "invalid_client", "Email belongs to an internal user.")

        access = self.client_tickets.get_access(project.id, client_user.id)
        if access is None:
            access = self.client_tickets.add_access(
                ProjectClientAccess(
                    organization_id=project.organization_id,
                    project_id=project.id,
                    client_user_id=client_user.id,
                    granted_by_id=actor.id,
                )
            )
        elif access.revoked_at is not None:
            access.revoked_at = None
            access.granted_by_id = actor.id
            self.db.add(access)
        self.db.commit()
        self.db.refresh(access)
        return access

    def list_project_clients(
        self, actor: User, project_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[tuple[ProjectClientAccess, User]], int]:
        """List project clients for owner/admin project settings."""
        project, membership = self._get_project_for_internal_member(actor, project_id)
        self._require_owner_admin(membership)
        return self.client_tickets.list_project_clients(project.id, limit, offset)

    def revoke_project_client(
        self, actor: User, project_id: uuid.UUID, client_access_id: uuid.UUID
    ) -> None:
        """Revoke future project ticket creation for one client access row."""
        project, membership = self._get_project_for_internal_member(actor, project_id)
        self._require_owner_admin(membership)
        access = self.client_tickets.get_access_by_id(project.id, client_access_id)
        if access is None:
            raise APIError(404, "client_access_not_found", "Client access was not found.")
        access.revoked_at = datetime.now(UTC)
        self.db.add(access)
        self.db.commit()

    def list_client_projects(self, actor: User) -> list[Project]:
        """List active projects available to a restricted client account."""
        self._require_client(actor)
        return self.client_tickets.list_client_projects(actor.id)

    def create_client_ticket(
        self,
        actor: User,
        project_id: uuid.UUID,
        *,
        subject: str,
        description: str,
        priority: str | None,
    ) -> Task:
        """Create a ticket task for a client's active project access."""
        self._require_client(actor)
        project = self._get_project_for_active_client(project_id, actor.id)
        if project.is_archived:
            raise APIError(409, "project_archived", "Archived projects cannot receive tickets.")
        ticket = Task(
            organization_id=project.organization_id,
            project_id=project.id,
            title=validate_task_title(subject),
            description=validate_ticket_body(description, code="invalid_ticket"),
            priority=parse_task_priority(priority, default=TaskPriority.MEDIUM),
            task_type=TaskType.TICKET,
            client_user_id=actor.id,
            created_by_id=actor.id,
        )
        self.tasks.add(ticket)
        recipients = set(self.client_tickets.list_owner_admin_user_ids(ticket.organization_id))
        recipients.update(self.projects.list_member_user_ids(ticket.project_id))
        NotificationService(self.db).notify_ticket_created(actor.id, ticket, recipients)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def list_project_tickets(
        self, actor: User, project_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[Task], int]:
        """List ticket tasks for an internal project member."""
        project, _ = self._get_project_for_internal_member(actor, project_id)
        return self.client_tickets.list_project_tickets(
            project.organization_id, project.id, limit, offset
        )

    def list_client_tickets(self, actor: User, limit: int, offset: int) -> tuple[list[Task], int]:
        """List only tickets created by the client actor."""
        self._require_client(actor)
        return self.client_tickets.list_client_tickets(actor.id, limit, offset)

    def get_internal_ticket(self, actor: User, ticket_id: uuid.UUID) -> Task:
        """Return one ticket for an internal member with project visibility."""
        ticket = self._get_ticket(ticket_id)
        self._get_project_for_internal_member(actor, ticket.project_id)
        return ticket

    def get_client_ticket(self, actor: User, ticket_id: uuid.UUID) -> Task:
        """Return one ticket only to the client who created it."""
        self._require_client(actor)
        ticket = self._get_ticket(ticket_id)
        if ticket.client_user_id != actor.id:
            raise APIError(404, "ticket_not_found", "Ticket was not found.")
        return ticket

    def update_ticket(
        self,
        actor: User,
        ticket_id: uuid.UUID,
        *,
        status: str | None,
        priority: str | None,
        assignee_id: uuid.UUID | None,
        fields_set: set[str],
    ) -> Task:
        """Update ticket fields allowed for owner/admins or the current assignee."""
        ticket = self._get_ticket(ticket_id)
        _, membership = self._get_project_for_internal_member(actor, ticket.project_id)
        if not fields_set:
            raise APIError(400, "invalid_ticket", "At least one field must be updated.")
        is_owner_admin = self._is_owner_admin(membership)
        if not is_owner_admin and ticket.assignee_id != actor.id:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
        if not is_owner_admin and "assignee_id" in fields_set:
            raise APIError(
                400,
                "invalid_assignment_request",
                "Assigned workers must request reassignment for another worker to accept.",
            )
        if "status" in fields_set:
            parsed_status = parse_task_status(status)
            if parsed_status is None:
                raise APIError(400, "invalid_ticket", "Ticket status is required.")
            ticket.status = parsed_status
        if "priority" in fields_set:
            parsed_priority = parse_task_priority(priority)
            if parsed_priority is None:
                raise APIError(400, "invalid_ticket", "Ticket priority is required.")
            ticket.priority = parsed_priority
        if "assignee_id" in fields_set:
            if assignee_id is not None:
                self._require_project_member(ticket.project_id, assignee_id)
            ticket.assignee_id = assignee_id
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)
        return ticket

    def create_assignment_request(
        self, actor: User, ticket_id: uuid.UUID, target_user_id: uuid.UUID
    ) -> TicketAssignmentRequest:
        """Ask another eligible project member to accept a ticket handoff."""
        ticket = self._get_ticket(ticket_id)
        self._get_project_for_internal_member(actor, ticket.project_id)
        if ticket.assignee_id != actor.id:
            raise APIError(403, "insufficient_role", "Only the assigned worker can hand off.")
        if target_user_id == actor.id:
            raise APIError(
                400,
                "invalid_assignment_request",
                "Target assignee must be a different project member.",
            )
        self._require_project_member(ticket.project_id, target_user_id)
        existing = self.client_tickets.get_pending_assignment_request(ticket.id, target_user_id)
        if existing is not None:
            return existing
        request = self.client_tickets.add_assignment_request(
            TicketAssignmentRequest(
                task_id=ticket.id,
                organization_id=ticket.organization_id,
                project_id=ticket.project_id,
                requested_by_id=actor.id,
                target_user_id=target_user_id,
            )
        )
        NotificationService(self.db).notify_ticket_assignment_requested(
            actor.id, ticket, target_user_id
        )
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_assignment_requests(
        self, actor: User, limit: int, offset: int
    ) -> tuple[list[TicketAssignmentRequest], int]:
        """List pending ticket handoffs for the current internal user."""
        if actor.account_type == UserAccountType.CLIENT:
            raise APIError(403, "internal_member_required", "Internal membership is required.")
        return self.client_tickets.list_assignment_requests_for_target(actor.id, limit, offset)

    def accept_assignment_request(
        self, actor: User, request_id: uuid.UUID
    ) -> TicketAssignmentRequest:
        """Accept a pending handoff and make the target worker the assignee."""
        request = self._get_assignment_request_for_target(actor, request_id)
        if request.status != TicketAssignmentRequestStatus.PENDING:
            raise APIError(
                400,
                "invalid_assignment_request",
                "Assignment request has already been resolved.",
            )
        ticket = self._get_ticket(request.task_id)
        self._get_project_for_internal_member(actor, ticket.project_id)
        self._require_project_member(ticket.project_id, actor.id)
        request.status = TicketAssignmentRequestStatus.ACCEPTED
        request.responded_at = datetime.now(UTC)
        ticket.assignee_id = actor.id
        self.db.add(request)
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(request)
        return request

    def decline_assignment_request(
        self, actor: User, request_id: uuid.UUID
    ) -> TicketAssignmentRequest:
        """Decline a pending handoff without changing the ticket assignee."""
        request = self._get_assignment_request_for_target(actor, request_id)
        if request.status != TicketAssignmentRequestStatus.PENDING:
            raise APIError(
                400,
                "invalid_assignment_request",
                "Assignment request has already been resolved.",
            )
        ticket = self._get_ticket(request.task_id)
        self._get_project_for_internal_member(actor, ticket.project_id)
        request.status = TicketAssignmentRequestStatus.DECLINED
        request.responded_at = datetime.now(UTC)
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def list_comments(
        self, actor: User, ticket_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[TicketComment], int]:
        """List ticket comments when the actor belongs to the conversation."""
        ticket = self._get_ticket_for_comment_actor(actor, ticket_id)
        return self.client_tickets.list_comments(ticket.id, limit, offset)

    def add_comment(self, actor: User, ticket_id: uuid.UUID, body: str) -> TicketComment:
        """Persist one ticket comment and create aggregate unread notifications."""
        ticket = self._get_ticket_for_comment_actor(actor, ticket_id, require_write=True)
        comment = self.client_tickets.add_comment(
            TicketComment(
                task_id=ticket.id,
                organization_id=ticket.organization_id,
                project_id=ticket.project_id,
                author_user_id=actor.id,
                body=validate_ticket_body(body),
            )
        )
        NotificationService(self.db).notify_ticket_comment(
            actor.id, ticket, self._ticket_comment_recipients(ticket)
        )
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def _get_project_for_internal_member(
        self, actor: User, project_id: uuid.UUID
    ) -> tuple[Project, OrganizationMembership]:
        """Load project context and reject restricted client accounts."""
        if actor.account_type == UserAccountType.CLIENT:
            raise APIError(403, "internal_member_required", "Internal membership is required.")
        result = self.projects.get_for_member(project_id, actor.id)
        if result is None:
            raise APIError(404, "project_not_found", "Project was not found.")
        project, membership = result
        if membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            if self.projects.get_membership(project.id, actor.id) is None:
                raise APIError(404, "project_not_found", "Project was not found.")
        return project, membership

    def _get_project_for_active_client(
        self, project_id: uuid.UUID, client_user_id: uuid.UUID
    ) -> Project:
        """Load a project only through active client access."""
        access = self.client_tickets.get_active_access(project_id, client_user_id)
        if access is None:
            raise APIError(409, "client_access_revoked", "Client project access is not active.")
        project = self.projects.get_by_id(access.organization_id, access.project_id)
        if project is None:
            raise APIError(404, "project_not_found", "Project was not found.")
        return project

    def _get_ticket(self, ticket_id: uuid.UUID) -> Task:
        """Return one ticket task or the stable not-found error."""
        ticket = self.client_tickets.get_ticket(ticket_id)
        if ticket is None:
            raise APIError(404, "ticket_not_found", "Ticket was not found.")
        return ticket

    def _get_assignment_request_for_target(
        self, actor: User, request_id: uuid.UUID
    ) -> TicketAssignmentRequest:
        """Return a handoff request only to its target worker."""
        if actor.account_type == UserAccountType.CLIENT:
            raise APIError(403, "internal_member_required", "Internal membership is required.")
        request = self.client_tickets.get_assignment_request_for_target(request_id, actor.id)
        if request is None:
            raise APIError(404, "assignment_request_not_found", "Assignment request was not found.")
        return request

    def _get_ticket_for_comment_actor(
        self, actor: User, ticket_id: uuid.UUID, *, require_write: bool = False
    ) -> Task:
        """Resolve ticket conversation access for clients and internal users."""
        ticket = self._get_ticket(ticket_id)
        if actor.account_type == UserAccountType.CLIENT:
            if ticket.client_user_id != actor.id:
                raise APIError(404, "ticket_not_found", "Ticket was not found.")
            return ticket
        _, membership = self._get_project_for_internal_member(actor, ticket.project_id)
        if membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            return ticket
        if ticket.assignee_id == actor.id:
            return ticket
        if require_write:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
        raise APIError(404, "ticket_not_found", "Ticket was not found.")

    def _require_project_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Validate ticket assignment targets against explicit project access."""
        project_membership = self.projects.get_membership(project_id, user_id)
        user = self.users.get_by_id(user_id)
        if (
            project_membership is None
            or self.organizations.get_membership(project_membership.organization_id, user_id)
            is None
            or user is None
            or user.account_type == UserAccountType.CLIENT
        ):
            raise APIError(400, "invalid_ticket", "Ticket assignee must be a project member.")

    def _ticket_comment_recipients(self, ticket: Task) -> set[uuid.UUID]:
        """Build the aggregate notification recipients for a ticket comment."""
        recipients = set(self.client_tickets.list_owner_admin_user_ids(ticket.organization_id))
        if ticket.assignee_id is not None:
            recipients.add(ticket.assignee_id)
        if ticket.client_user_id is not None:
            recipients.add(ticket.client_user_id)
        return recipients

    @staticmethod
    def _is_owner_admin(membership: OrganizationMembership) -> bool:
        """Return whether a membership can directly manage ticket assignment."""
        return membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN}

    @staticmethod
    def _require_owner_admin(membership: OrganizationMembership) -> None:
        """Raise a stable error when a member cannot manage project clients."""
        if not ClientTicketService._is_owner_admin(membership):
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")

    @staticmethod
    def _require_client(actor: User) -> None:
        """Reject internal accounts from client-only endpoints."""
        if actor.account_type != UserAccountType.CLIENT:
            raise APIError(403, "client_account_required", "A client account is required.")
