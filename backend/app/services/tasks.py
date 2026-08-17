"""Task business rules, assignment policy, and status transitions."""

import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.jobs.enqueue import enqueue_task_assignment_notification
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import Project, Task, TaskPriority, TaskStatus, TaskType
from app.models.user import User
from app.repositories.organizations import OrganizationRepository
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository
from app.services.metadata import non_negative_decimal, optional_string
from app.services.notifications import NotificationService

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


def parse_task_type(value: str | None, *, default: TaskType | None = None) -> TaskType | None:
    """Convert public task type text into the internal enum."""
    if value is None:
        return default
    try:
        return TaskType(value)
    except ValueError as exc:
        raise APIError(400, "invalid_task", "Task type is invalid.") from exc


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
        estimated_hours: Decimal | None,
        actual_hours: Decimal | None,
        sort_order: int | None,
        blocked_reason: str | None,
        external_reference: str | None,
        task_type: str | None,
        watcher_ids: list[uuid.UUID] | None,
    ) -> Task:
        """Create a task in a non-archived project after assignment validation."""
        project, membership = self._get_project_for_member(project_id, actor.id)
        if project.is_archived:
            raise APIError(409, "project_archived", "Archived projects cannot receive new tasks.")
        self._validate_create_assignment(actor, membership, assignee_id)
        if assignee_id is not None:
            self._require_project_member(project.id, assignee_id)

        task = Task(
            organization_id=project.organization_id,
            project_id=project.id,
            title=validate_task_title(title),
            description=description,
            priority=parse_task_priority(priority, default=TaskPriority.MEDIUM),
            assignee_id=assignee_id,
            due_date=due_date,
            estimated_hours=non_negative_decimal(
                estimated_hours, code="invalid_task", field="estimated_hours"
            ),
            actual_hours=non_negative_decimal(
                actual_hours, code="invalid_task", field="actual_hours"
            ),
            sort_order=sort_order,
            external_reference=optional_string(
                external_reference,
                max_length=200,
                code="invalid_task",
                field="external_reference",
            ),
            task_type=self._parse_internal_task_type(task_type),
            created_by_id=actor.id,
        )
        self._apply_blocked_reason(task, blocked_reason, blocked_reason_provided=True)
        normalized_watchers = self._validate_watcher_ids(project.organization_id, watcher_ids or [])
        self.tasks.add(task)
        self.tasks.replace_watchers(task, normalized_watchers, actor.id)
        if normalized_watchers:
            logger.info(
                "task watchers changed actor_id=%s organization_id=%s task_id=%s watcher_count=%s",
                actor.id,
                task.organization_id,
                task.id,
                len(normalized_watchers),
            )
        NotificationService(self.db).notify_task_created_or_assigned(actor.id, task, created=True)
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
        task_type: str | None,
        watcher_id: uuid.UUID | None,
        external_reference: str | None,
        label_id: uuid.UUID | None,
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
            task_type=parse_task_type(task_type),
            watcher_id=watcher_id,
            external_reference=optional_string(
                external_reference,
                max_length=200,
                code="invalid_task",
                field="external_reference",
            ),
            label_id=label_id,
        )

    def get_task(self, actor: User, task_id: uuid.UUID) -> tuple[Task, OrganizationMembership]:
        """Return task details or hide missing and cross-tenant resources."""
        result = self.tasks.get_for_member(task_id, actor.id)
        if result is None:
            raise APIError(404, "task_not_found", "Task was not found.")
        task, membership = result
        if membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            if self.projects.get_membership(task.project_id, actor.id) is None:
                raise APIError(404, "task_not_found", "Task was not found.")
        return task, membership

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
        estimated_hours: Decimal | None,
        actual_hours: Decimal | None,
        sort_order: int | None,
        blocked_reason: str | None,
        external_reference: str | None,
        task_type: str | None,
        watcher_ids: list[uuid.UUID] | None,
        fields_set: set[str],
    ) -> Task:
        """Update a task after role, assignment, and transition checks."""
        task, membership = self.get_task(actor, task_id)
        self._validate_update_permission(actor, membership, task, fields_set)
        if not fields_set:
            raise APIError(400, "invalid_task", "At least one field must be updated.")
        assignment_changed = False
        status_changed = False
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
                self._require_project_member(task.project_id, assignee_id)
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
        if "estimated_hours" in fields_set:
            task.estimated_hours = non_negative_decimal(
                estimated_hours, code="invalid_task", field="estimated_hours"
            )
        if "actual_hours" in fields_set:
            task.actual_hours = non_negative_decimal(
                actual_hours, code="invalid_task", field="actual_hours"
            )
        if "sort_order" in fields_set:
            task.sort_order = sort_order
        if "external_reference" in fields_set:
            task.external_reference = optional_string(
                external_reference,
                max_length=200,
                code="invalid_task",
                field="external_reference",
            )
        if "task_type" in fields_set:
            parsed_type = self._parse_internal_task_type(task_type, required=True)
            if parsed_type is None:
                raise APIError(400, "invalid_task", "Task type is required.")
            task.task_type = parsed_type
        if "status" in fields_set:
            parsed_status = parse_task_status(status)
            if parsed_status is None:
                raise APIError(400, "invalid_task", "Task status is required.")
            previous_status = task.status
            self._apply_status_transition(task, parsed_status)
            status_changed = previous_status != task.status
        self._apply_blocked_reason(
            task,
            blocked_reason,
            blocked_reason_provided="blocked_reason" in fields_set,
        )
        if "watcher_ids" in fields_set:
            normalized_watchers = self._validate_watcher_ids(
                task.organization_id, watcher_ids or []
            )
            self.tasks.replace_watchers(task, normalized_watchers, actor.id)
            logger.info(
                "task watchers changed actor_id=%s organization_id=%s task_id=%s watcher_count=%s",
                actor.id,
                task.organization_id,
                task.id,
                len(normalized_watchers),
            )

        self.db.add(task)
        notifier = NotificationService(self.db)
        if assignment_changed:
            notifier.notify_task_created_or_assigned(actor.id, task, created=False)
        if status_changed:
            notifier.notify_task_status_changed(actor.id, task)
        self.db.commit()
        self.db.refresh(task)
        if assignment_changed and task.assignee_id is not None:
            enqueue_task_assignment_notification(task)
        return task

    def list_watcher_user_ids(self, task_id: uuid.UUID) -> list[uuid.UUID]:
        """Expose watcher identifiers for API response construction."""
        return self.tasks.list_watcher_user_ids(task_id)

    def _get_project_for_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[Project, OrganizationMembership]:
        """Load a project only when the actor belongs to its organization."""
        result = self.projects.get_for_member(project_id, user_id)
        if result is None:
            raise APIError(404, "project_not_found", "Project was not found.")
        project, membership = result
        self._require_project_access(project, membership, user_id)
        return project, membership

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

    def _require_project_member(self, project_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Validate assignment targets against explicit project access."""
        project_membership = self.projects.get_membership(project_id, user_id)
        if (
            project_membership is None
            or self.organizations.get_membership(project_membership.organization_id, user_id)
            is None
        ):
            raise APIError(
                400,
                "invalid_task",
                "Task assignee must be a project member.",
            )

    def _validate_watcher_ids(
        self, organization_id: uuid.UUID, watcher_ids: list[uuid.UUID]
    ) -> list[uuid.UUID]:
        """Validate and de-duplicate watcher IDs inside the task organization."""
        normalized: list[uuid.UUID] = []
        seen: set[uuid.UUID] = set()
        for watcher_id in watcher_ids:
            if watcher_id in seen:
                continue
            seen.add(watcher_id)
            if self.organizations.get_membership(organization_id, watcher_id) is None:
                raise APIError(400, "invalid_task", "Task watchers must be organization members.")
            normalized.append(watcher_id)
        return normalized

    def _require_project_access(
        self, project: Project, membership: OrganizationMembership, user_id: uuid.UUID
    ) -> None:
        """Hide project tasks from regular members without explicit access."""
        if membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            return
        if self.projects.get_membership(project.id, user_id) is None:
            raise APIError(404, "project_not_found", "Project was not found.")

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

    @staticmethod
    def _apply_blocked_reason(
        task: Task, blocked_reason: str | None, *, blocked_reason_provided: bool
    ) -> None:
        """Keep blocker text only while a task remains in blocked status."""
        if task.status != TaskStatus.BLOCKED:
            if blocked_reason_provided and blocked_reason not in {None, ""}:
                raise APIError(400, "invalid_task", "Blocked reason requires blocked status.")
            task.blocked_reason = None
            return
        if blocked_reason_provided:
            task.blocked_reason = optional_string(
                blocked_reason, max_length=1000, code="invalid_task", field="blocked_reason"
            )

    @staticmethod
    def _parse_internal_task_type(value: str | None, *, required: bool = False) -> TaskType | None:
        """Keep ticket creation on SPEC-305 ticket endpoints, not generic tasks."""
        parsed = parse_task_type(value, default=TaskType.INTERNAL if not required else None)
        if parsed == TaskType.TICKET:
            raise APIError(400, "invalid_task", "Tickets must be created through ticket APIs.")
        return parsed
