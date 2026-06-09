from app.api.health import health
from app.main import app


def test_health_route_is_registered() -> None:
    paths = {route.path for route in app.routes}

    assert "/health" in paths


def test_health_returns_ok() -> None:
    assert health() == {"status": "ok"}
