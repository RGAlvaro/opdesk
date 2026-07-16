"""Safe enqueue helpers called from request-time service code."""

import logging

from app.models.project import Task
from app.notifications.assignment import build_task_assignment_notification_payload

logger = logging.getLogger(__name__)


def enqueue_task_assignment_notification(task: Task) -> bool:
    """Publish a task assignment notification job without exposing delivery details."""
    if task.assignee_id is None:
        return False

    from app.jobs.tasks import send_task_assignment_notification

    payload = build_task_assignment_notification_payload(task)
    try:
        send_task_assignment_notification.delay(
            str(payload.task_id),
            str(payload.assignee_id),
            payload.assignment_version,
        )
    except Exception as exc:
        logger.exception(
            "task_assignment_notification enqueue_failed task_id=%s assignee_id=%s error_class=%s",
            payload.task_id,
            payload.assignee_id,
            exc.__class__.__name__,
        )
        return False
    return True
