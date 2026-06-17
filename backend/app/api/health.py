"""Infrastructure health endpoint used by smoke checks and containers."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    """Return a minimal liveness response for local and deployment checks."""
    return {"status": "ok"}
