"""Health endpoint tests for routing and response shape."""

from app.api.health import health
from app.main import app


def test_health_route_is_registered() -> None:
    """The FastAPI app exposes the infrastructure health route."""
    paths = {route.path for route in app.routes}

    assert "/health" in paths


def test_health_returns_ok() -> None:
    """The health handler returns the expected liveness payload."""
    assert health() == {"status": "ok"}
