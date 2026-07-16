"""Task assignment notification payloads and local-safe delivery."""

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.project import Task
from app.models.user import User
from app.repositories.tasks import TaskRepository
from app.repositories.users import UserRepository

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TaskAssignmentNotificationPayload:
    """Minimal safe payload for notifying one task assignee."""

    task_id: uuid.UUID
    assignee_id: uuid.UUID
    assignment_version: str


class ConsoleAssignmentNotificationSender:
    """Deliver assignment notifications through structured application logs."""

    def send(self, task: Task, assignee: User, payload: TaskAssignmentNotificationPayload) -> None:
        """Record the notification intent without contacting an external provider."""
        logger.info(
            "task_assignment_notification delivered task_id=%s assignee_id=%s "
            "organization_id=%s assignment_version=%s",
            task.id,
            assignee.id,
            task.organization_id,
            payload.assignment_version,
        )


def build_task_assignment_notification_payload(task: Task) -> TaskAssignmentNotificationPayload:
    """Create a minimal assignment payload from a persisted task."""
    if task.assignee_id is None:
        raise ValueError("Task assignment notifications require an assignee.")
    if task.updated_at is None:
        raise ValueError("Task assignment notifications require an updated_at version.")
    return TaskAssignmentNotificationPayload(
        task_id=task.id,
        assignee_id=task.assignee_id,
        assignment_version=task.updated_at.isoformat(),
    )


def process_task_assignment_notification(
    db: Session,
    payload: TaskAssignmentNotificationPayload,
    *,
    sender: ConsoleAssignmentNotificationSender | None = None,
) -> str:
    """Load current task state and deliver or ignore a stale assignment notification."""
    task = TaskRepository(db).get_by_id_for_notification(payload.task_id)
    if task is None:
        logger.warning(
            "task_assignment_notification stale_missing_task task_id=%s assignee_id=%s",
            payload.task_id,
            payload.assignee_id,
        )
        return "stale"
    if task.assignee_id != payload.assignee_id:
        logger.warning(
            "task_assignment_notification stale_assignee task_id=%s payload_assignee_id=%s "
            "current_assignee_id=%s",
            payload.task_id,
            payload.assignee_id,
            task.assignee_id,
        )
        return "stale"
    current_assignment_version = task.updated_at.isoformat()
    if current_assignment_version != payload.assignment_version:
        logger.warning(
            "task_assignment_notification stale_version task_id=%s assignee_id=%s "
            "payload_assignment_version=%s current_assignment_version=%s",
            payload.task_id,
            payload.assignee_id,
            payload.assignment_version,
            current_assignment_version,
        )
        return "stale"

    assignee = UserRepository(db).get_by_id(payload.assignee_id)
    if assignee is None:
        logger.warning(
            "task_assignment_notification stale_missing_assignee task_id=%s assignee_id=%s",
            payload.task_id,
            payload.assignee_id,
        )
        return "stale"

    delivery = sender or ConsoleAssignmentNotificationSender()
    delivery.send(task, assignee, payload)
    return "delivered"
