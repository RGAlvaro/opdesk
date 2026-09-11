"""Shared pytest safeguards for backend tests that should stay network-free."""

import uuid

import pytest


@pytest.fixture(autouse=True)
def disable_external_notification_broker(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep post-commit email delivery fan-out from contacting Celery in unit tests."""
    import app.jobs.enqueue as enqueue_module

    def fake_enqueue_external_notification_delivery(delivery_id: uuid.UUID) -> bool:
        """Accept a queued delivery id without opening broker connections."""
        return delivery_id is not None

    monkeypatch.setattr(
        enqueue_module,
        "enqueue_external_notification_delivery",
        fake_enqueue_external_notification_delivery,
    )
