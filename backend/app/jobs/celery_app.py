"""Celery application configured from OpsDesk backend settings."""

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
    enable_utc=True,
    result_serializer="json",
    task_always_eager=settings.celery_task_always_eager,
    task_default_queue="opdesk",
    task_eager_propagates=settings.celery_task_eager_propagates,
    task_serializer="json",
    timezone="UTC",
)
