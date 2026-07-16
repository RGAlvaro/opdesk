"""Task business rules, assignment policy, and status transitions."""

import logging
import uuid
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.jobs.enqueue import enqueue_task_assignment_notification
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import Project, Task, TaskPriority, TaskStatus
from app.models.user import User
from app.repositories.organizations import OrganizationRepository
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository

logger = logging.getLogger(__name__)


def validate_task_title(title: str) -> str:
    """Normalize and validate a task title for persistence."""
    normalized = " ".join(title.strip().split())
    if not normalized or len(normalized) > 200:
        raise APIError(400, "invalid_task", "Title must be between 1 and 200 characters.")
    return normalized


def parse_task_status(value: str | None, *, default: TaskStatus | None = None) -> TaskStatus | None:
    """Convert public status text into the internal enum or raise a business error."""
    if value is None:
        return default
    try:
        return TaskStatus(value)
    except ValueError as exc:
        raise APIError(400, "invalid_task", "Task status is invalid.") from exc


def parse_task_priority(
    value: str | None, *, default: TaskPriority | None = None
) -> TaskPriority | None:
    """Convert public priority text into the internal enum or raise a business error."""
    if value is None:
        return default
    try:
        return TaskPriority(value)
    except ValueError as exc:
        raise APIError(400, "invalid_task", "Task priority is invalid.") from exc


class TaskService:
    """Coordinate task persistence with tenant, role, and assignment rules."""

    def __init__(self, db: Session) -> None:
        """Create task collaborators bound to the request transaction."""
        self.db = db
        self.organizations = OrganizationRepository(db)
        self.projects = ProjectRepository(db)
        self.tasks = TaskRepository(db)

    def create_task(
        self,
        actor: User,
        project_id: uuid.UUID,
        *,
        title: str,
        description: str | None,
        priority: str | None,
        assignee_id: uuid.UUID | None,
        due_date: date | None,
    ) -> Task:
        """Create a task in a non-archived project after assignment validation."""
        project, membership = self._get_project_for_member(project_id, actor.id)
        if project.is_archived:
            raise APIError(409, "project_archived", "Archived projects cannot receive new tasks.")
        self._validate_create_assignment(actor, membership, assignee_id)
        if assignee_id is not None:
            self._require_organization_member(project.organization_id, assignee_id)

        task = Task(
            organization_id=project.organization_id,
            project_id=project.id,
            title=validate_task_title(title),
            description=description,
            priority=parse_task_priority(priority, default=TaskPriority.MEDIUM),
            assignee_id=assignee_id,
            due_date=due_date,
            created_by_id=actor.id,
        )
        self.tasks.add(task)
        self.db.commit()
        self.db.refresh(task)
        if task.assignee_id is not None:
            enqueue_task_assignment_notification(task)
        return task

    def list_tasks(
        self,
        actor: User,
        project_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
        status: str | None,
        assignee_id: uuid.UUID | None,
        priority: str | None,
        due_before: date | None,
        due_after: date | None,
    ) -> tuple[list[Task], int]:
        """List tasks for project members with documented filters."""
        project, _ = self._get_project_for_member(project_id, actor.id)
        return self.tasks.list_by_project(
            project.organization_id,
            project.id,
            limit=limit,
            offset=offset,
            status=parse_task_status(status),
            assignee_id=assignee_id,
            priority=parse_task_priority(priority),
            due_before=due_before,
            due_after=due_after,
        )

    def get_task(self, actor: User, task_id: uuid.UUID) -> tuple[Task, OrganizationMembership]:
        """Return task details or hide missing and cross-tenant resources."""
        result = self.tasks.get_for_member(task_id, actor.id)
        if result is None:
            raise APIError(404, "task_not_found", "Task was not found.")
        return result

    def update_task(
        self,
        actor: User,
        task_id: uuid.UUID,
        *,
        title: str | None,
        description: str | None,
        status: str | None,
        priority: str | None,
        assignee_id: uuid.UUID | None,
        due_date: date | None,
        fields_set: set[str],
    ) -> Task:
        """Update a task after role, assignment, and transition checks."""
        task, membership = self.get_task(actor, task_id)
        self._validate_update_permission(actor, membership, task, fields_set)
        if not fields_set:
            raise APIError(400, "invalid_task", "At least one field must be updated.")
        assignment_changed = False
        if "title" in fields_set:
            if title is None:
                raise APIError(400, "invalid_task", "Title is required.")
            task.title = validate_task_title(title)
        if "description" in fields_set:
            task.description = description
        if "priority" in fields_set:
            parsed_priority = parse_task_priority(priority)
            if parsed_priority is None:
                raise APIError(400, "invalid_task", "Task priority is required.")
            task.priority = parsed_priority
        if "assignee_id" in fields_set:
            if assignee_id is not None:
                self._require_organization_member(task.organization_id, assignee_id)
            previous_assignee_id = task.assignee_id
            task.assignee_id = assignee_id
            if previous_assignee_id != assignee_id:
                assignment_changed = True
                logger.info(
                    "task assignment changed actor_id=%s organization_id=%s task_id=%s "
                    "old_assignee_id=%s new_assignee_id=%s",
                    actor.id,
                    task.organization_id,
                    task.id,
                    previous_assignee_id,
                    assignee_id,
                )
        if "due_date" in fields_set:
            task.due_date = due_date
        if "status" in fields_set:
            parsed_status = parse_task_status(status)
            if parsed_status is None:
                raise APIError(400, "invalid_task", "Task status is required.")
            self._apply_status_transition(task, parsed_status)

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        if assignment_changed and task.assignee_id is not None:
            enqueue_task_assignment_notification(task)
        return task

    def _get_project_for_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[Project, OrganizationMembership]:
        """Load a project only when the actor belongs to its organization."""
        result = self.projects.get_for_member(project_id, user_id)
        if result is None:
            raise APIError(404, "project_not_found", "Project was not found.")
        return result

    def _require_organization_member(
        self, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationMembership:
        """Validate assignee membership inside the task organization."""
        membership = self.organizations.get_membership(organization_id, user_id)
        if membership is None:
            raise APIError(
                400,
                "invalid_task",
                "Task assignee must be a member of the task organization.",
            )
        return membership

    @staticmethod
    def _validate_create_assignment(
        actor: User, membership: OrganizationMembership, assignee_id: uuid.UUID | None
    ) -> None:
        """Enforce member assignment limits during task creation."""
        if membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            return
        if assignee_id is not None and assignee_id != actor.id:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")

    @staticmethod
    def _validate_update_permission(
        actor: User, membership: OrganizationMembership, task: Task, fields_set: set[str]
    ) -> None:
        """Enforce task update ownership and member reassignment restrictions."""
        if membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            return
        if task.assignee_id != actor.id:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
        if "assignee_id" in fields_set:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")

    @staticmethod
    def _apply_status_transition(task: Task, new_status: TaskStatus) -> None:
        """Maintain completion timestamp when entering or leaving done."""
        previous_status = task.status
        task.status = new_status
        if previous_status != TaskStatus.DONE and new_status == TaskStatus.DONE:
            task.completed_at = datetime.now(UTC)
        elif previous_status == TaskStatus.DONE and new_status != TaskStatus.DONE:
            task.completed_at = None
