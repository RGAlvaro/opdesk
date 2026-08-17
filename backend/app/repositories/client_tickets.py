"""Data access helpers for project client access and ticket comments."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import (
    Project,
    ProjectClientAccess,
    ProjectMembership,
    Task,
    TaskType,
    TicketAssignmentRequest,
    TicketAssignmentRequestStatus,
    TicketComment,
)
from app.models.user import User, UserAccountType


class ClientTicketRepository:
    """Keep client ticket queries scoped by project, organization, and actor."""

    def __init__(self, db: Session) -> None:
        """Store the request database session."""
        self.db = db

    def add_access(self, access: ProjectClientAccess) -> ProjectClientAccess:
        """Stage and flush one project client access row."""
        self.db.add(access)
        self.db.flush()
        return access

    def add_comment(self, comment: TicketComment) -> TicketComment:
        """Stage and flush one ticket comment row."""
        self.db.add(comment)
        self.db.flush()
        return comment

    def add_assignment_request(self, request: TicketAssignmentRequest) -> TicketAssignmentRequest:
        """Stage and flush one ticket reassignment request."""
        self.db.add(request)
        self.db.flush()
        return request

    def get_access_by_id(
        self, project_id: uuid.UUID, access_id: uuid.UUID
    ) -> ProjectClientAccess | None:
        """Load one project client access row by public identifier."""
        return self.db.scalar(
            select(ProjectClientAccess).where(
                ProjectClientAccess.id == access_id,
                ProjectClientAccess.project_id == project_id,
            )
        )

    def get_access(
        self, project_id: uuid.UUID, client_user_id: uuid.UUID
    ) -> ProjectClientAccess | None:
        """Return a client's access row for one project when it exists."""
        return self.db.scalar(
            select(ProjectClientAccess).where(
                ProjectClientAccess.project_id == project_id,
                ProjectClientAccess.client_user_id == client_user_id,
            )
        )

    def get_active_access(
        self, project_id: uuid.UUID, client_user_id: uuid.UUID
    ) -> ProjectClientAccess | None:
        """Return project access only when it has not been revoked."""
        return self.db.scalar(
            select(ProjectClientAccess).where(
                ProjectClientAccess.project_id == project_id,
                ProjectClientAccess.client_user_id == client_user_id,
                ProjectClientAccess.revoked_at.is_(None),
            )
        )

    def list_project_clients(
        self, project_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[tuple[ProjectClientAccess, User]], int]:
        """List project client access records with client user details."""
        filters = [ProjectClientAccess.project_id == project_id]
        total = self.db.scalar(select(func.count(ProjectClientAccess.id)).where(*filters)) or 0
        rows = self.db.execute(
            select(ProjectClientAccess, User)
            .join(User, User.id == ProjectClientAccess.client_user_id)
            .where(*filters)
            .order_by(ProjectClientAccess.created_at, ProjectClientAccess.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return [(row[0], row[1]) for row in rows], total

    def list_client_projects(self, client_user_id: uuid.UUID) -> list[Project]:
        """List projects where a client has active access."""
        return list(
            self.db.scalars(
                select(Project)
                .join(ProjectClientAccess, ProjectClientAccess.project_id == Project.id)
                .where(
                    ProjectClientAccess.client_user_id == client_user_id,
                    ProjectClientAccess.revoked_at.is_(None),
                )
                .order_by(Project.created_at, Project.id)
            )
        )

    def list_project_tickets(
        self, organization_id: uuid.UUID, project_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[Task], int]:
        """List ticket tasks for one internal project surface."""
        filters = [
            Task.organization_id == organization_id,
            Task.project_id == project_id,
            Task.task_type == TaskType.TICKET,
        ]
        total = self.db.scalar(select(func.count(Task.id)).where(*filters)) or 0
        tickets = list(
            self.db.scalars(
                select(Task)
                .where(*filters)
                .order_by(Task.created_at.desc(), Task.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return tickets, total

    def list_client_tickets(
        self, client_user_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[Task], int]:
        """List ticket tasks created by one client account."""
        filters = [Task.client_user_id == client_user_id, Task.task_type == TaskType.TICKET]
        total = self.db.scalar(select(func.count(Task.id)).where(*filters)) or 0
        tickets = list(
            self.db.scalars(
                select(Task)
                .where(*filters)
                .order_by(Task.created_at.desc(), Task.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        return tickets, total

    def get_ticket(self, ticket_id: uuid.UUID) -> Task | None:
        """Load a task only when it is a client ticket."""
        return self.db.scalar(
            select(Task).where(Task.id == ticket_id, Task.task_type == TaskType.TICKET)
        )

    def get_pending_assignment_request(
        self, ticket_id: uuid.UUID, target_user_id: uuid.UUID
    ) -> TicketAssignmentRequest | None:
        """Return an existing pending handoff for one ticket and target worker."""
        return self.db.scalar(
            select(TicketAssignmentRequest).where(
                TicketAssignmentRequest.task_id == ticket_id,
                TicketAssignmentRequest.target_user_id == target_user_id,
                TicketAssignmentRequest.status == TicketAssignmentRequestStatus.PENDING,
            )
        )

    def get_assignment_request_for_target(
        self, request_id: uuid.UUID, target_user_id: uuid.UUID
    ) -> TicketAssignmentRequest | None:
        """Load a handoff request only for the user expected to answer it."""
        return self.db.scalar(
            select(TicketAssignmentRequest).where(
                TicketAssignmentRequest.id == request_id,
                TicketAssignmentRequest.target_user_id == target_user_id,
            )
        )

    def list_assignment_requests_for_target(
        self, target_user_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[TicketAssignmentRequest], int]:
        """List pending handoffs only while the target still has project access."""
        filters = [
            TicketAssignmentRequest.target_user_id == target_user_id,
            TicketAssignmentRequest.status == TicketAssignmentRequestStatus.PENDING,
            Task.task_type == TaskType.TICKET,
        ]
        base_statement = (
            select(TicketAssignmentRequest)
            .join(Task, Task.id == TicketAssignmentRequest.task_id)
            .join(
                ProjectMembership,
                (ProjectMembership.project_id == TicketAssignmentRequest.project_id)
                & (ProjectMembership.user_id == TicketAssignmentRequest.target_user_id),
            )
            .join(
                OrganizationMembership,
                (OrganizationMembership.organization_id == TicketAssignmentRequest.organization_id)
                & (OrganizationMembership.user_id == TicketAssignmentRequest.target_user_id),
            )
            .where(*filters)
        )
        total = self.db.scalar(select(func.count()).select_from(base_statement.subquery())) or 0
        requests = list(
            self.db.scalars(
                base_statement.order_by(
                    TicketAssignmentRequest.created_at.desc(), TicketAssignmentRequest.id
                )
                .limit(limit)
                .offset(offset)
            )
        )
        return requests, total

    def list_comments(
        self, ticket_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[TicketComment], int]:
        """List non-deleted comments for one ticket conversation."""
        filters = [TicketComment.task_id == ticket_id, TicketComment.deleted_at.is_(None)]
        total = self.db.scalar(select(func.count(TicketComment.id)).where(*filters)) or 0
        comments = list(
            self.db.scalars(
                select(TicketComment)
                .where(*filters)
                .order_by(TicketComment.created_at, TicketComment.id)
                .limit(limit)
                .offset(offset)
            )
        )
        return comments, total

    def list_owner_admin_user_ids(self, organization_id: uuid.UUID) -> list[uuid.UUID]:
        """Return owner/admin users for project-lead ticket notifications."""
        return list(
            self.db.scalars(
                select(OrganizationMembership.user_id).where(
                    OrganizationMembership.organization_id == organization_id,
                    OrganizationMembership.role.in_([MembershipRole.OWNER, MembershipRole.ADMIN]),
                )
            )
        )

    def is_client_account(self, user: User) -> bool:
        """Return whether a user is restricted to client surfaces."""
        return user.account_type == UserAccountType.CLIENT
