"""Application-specific API errors and their JSON response adapter."""

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


class APIError(Exception):
    """Represent an API error that follows the repository-wide error contract."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


async def api_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Convert APIError exceptions into the stable JSON error envelope."""
    if not isinstance(exc, APIError):
        raise exc
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
