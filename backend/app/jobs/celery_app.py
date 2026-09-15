"""Celery application configured from OpsDesk backend settings."""

from datetime import timedelta

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "opdesk",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.jobs.tasks"],
)
celery_app.conf.update(
    accept_content=["json"],
    beat_schedule={
        "scheduler-heartbeat": {
            "task": "operational.scheduler_heartbeat",
            "schedule": timedelta(minutes=5),
        },
        "external-delivery-retry-sweep": {
            "task": "operational.external_delivery_retry_sweep",
            "schedule": timedelta(minutes=5),
        },
        "expired-invitation-maintenance": {
            "task": "operational.expired_invitation_maintenance",
            "schedule": timedelta(hours=1),
        },
        "stale-ticket-assignment-request-reminders": {
            "task": "operational.stale_ticket_assignment_request_reminders",
            "schedule": timedelta(hours=6),
        },
    },
    enable_utc=True,
    result_serializer="json",
    task_always_eager=settings.celery_task_always_eager,
    task_default_queue="opdesk",
    task_eager_propagates=settings.celery_task_eager_propagates,
    task_serializer="json",
    timezone="UTC",
)
