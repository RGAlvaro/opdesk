"""Celery tasks for background notification work."""

import logging
import uuid

from app.db.session import SessionLocal
from app.jobs.celery_app import celery_app
from app.notifications.assignment import (
    TaskAssignmentNotificationPayload,
    process_task_assignment_notification,
)
from app.notifications.delivery import ExternalNotificationDeliveryService

logger = logging.getLogger(__name__)


@celery_app.task(  # type: ignore[untyped-decorator]
    bind=True,
    name="notifications.task_assignment",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
)
def send_task_assignment_notification(
    self: object, task_id: str, assignee_id: str, assignment_version: str
) -> str:
    """Process one task assignment notification from safe resource identifiers."""
    try:
        payload = TaskAssignmentNotificationPayload(
            task_id=uuid.UUID(task_id),
            assignee_id=uuid.UUID(assignee_id),
            assignment_version=assignment_version,
        )
    except ValueError as exc:
        logger.warning(
            "task_assignment_notification invalid_payload task_id=%s assignee_id=%s error_class=%s",
            task_id,
            assignee_id,
            exc.__class__.__name__,
        )
        return "invalid"
    db = SessionLocal()
    try:
        return process_task_assignment_notification(db, payload)
    except Exception as exc:
        logger.exception(
            "task_assignment_notification failed task_id=%s assignee_id=%s error_class=%s",
            payload.task_id,
            payload.assignee_id,
            exc.__class__.__name__,
        )
        raise
    finally:
        db.close()


@celery_app.task(  # type: ignore[untyped-decorator]
    name="notifications.external_delivery",
)
def send_external_notification_delivery(delivery_id: str) -> str:
    """Process one external notification delivery audit row."""
    try:
        parsed_delivery_id = uuid.UUID(delivery_id)
    except ValueError as exc:
        logger.warning(
            "external_notification_delivery invalid_payload delivery_id=%s error_class=%s",
            delivery_id,
            exc.__class__.__name__,
        )
        return "invalid"
    db = SessionLocal()
    try:
        result = ExternalNotificationDeliveryService(db).process_delivery(parsed_delivery_id)
        logger.info(
            "external_notification_delivery processed delivery_id=%s result=%s",
            parsed_delivery_id,
            result,
        )
        return result
    except Exception as exc:
        logger.exception(
            "external_notification_delivery failed delivery_id=%s error_class=%s",
            parsed_delivery_id,
            exc.__class__.__name__,
        )
        raise
    finally:
        db.close()


@celery_app.task(  # type: ignore[untyped-decorator]
    name="notifications.external_delivery_due",
)
def process_due_external_notification_deliveries(limit: int = 100) -> int:
    """Sweep pending external deliveries whose retry time has arrived."""
    db = SessionLocal()
    try:
        processed = ExternalNotificationDeliveryService(db).process_due_deliveries(limit)
        logger.info("external_notification_delivery due_processed count=%s", processed)
        return processed
    finally:
        db.close()
