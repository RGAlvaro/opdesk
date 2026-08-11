"""Create and configure the FastAPI application used by every runtime entry point."""

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.errors import APIError, api_error_handler
from app.api.health import router as health_router
from app.api.labels import router as labels_router
from app.api.organizations import router as organizations_router
from app.api.projects import router as projects_router
from app.api.tasks import router as tasks_router
from app.api.users import router as users_router


def create_app() -> FastAPI:
    """Build the API app with shared error handling and versioned routers."""
    app = FastAPI(title="OpsDesk API")
    app.add_exception_handler(APIError, api_error_handler)
    app.include_router(auth_router)
    app.include_router(health_router)
    app.include_router(labels_router)
    app.include_router(organizations_router)
    app.include_router(projects_router)
    app.include_router(tasks_router)
    app.include_router(users_router)
    return app


app = create_app()
