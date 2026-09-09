"""HTTP endpoints for the authenticated in-app notification inbox."""

import uuid
from collections import defaultdict
from typing import Annotated, Any

import anyio
from fastapi import APIRouter, Depends, Query, Response, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.errors import APIError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.user import User
from app.repositories.users import UserRepository
from app.schemas.notifications import (
    NotificationListResponse,
    NotificationRead,
    NotificationUnreadCountResponse,
    NotificationUpdateRequest,
)
from app.services.notifications import NotificationService, set_notification_event_publisher
from app.services.security import decode_token

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationConnectionManager:
    """Track in-process notification WebSockets by recipient user."""

    def __init__(self) -> None:
        """Create an empty current-process connection registry."""
        self.connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, recipient_user_id: uuid.UUID, websocket: WebSocket) -> None:
        """Accept and register one authenticated notification socket."""
        await websocket.accept()
        self.connections[recipient_user_id].add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a socket from every recipient registry."""
        for recipient_user_id in list(self.connections):
            sockets = self.connections[recipient_user_id]
            sockets.discard(websocket)
            if not sockets:
                del self.connections[recipient_user_id]

    async def broadcast(self, recipient_user_id: uuid.UUID, payload: dict[str, Any]) -> None:
        """Send one JSON event to active sockets for the exact recipient."""
        stale: list[WebSocket] = []
        for websocket in self.connections.get(recipient_user_id, set()).copy():
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)

    def publish_from_sync(self, recipient_user_id: uuid.UUID, payload: dict[str, Any]) -> None:
        """Bridge synchronous domain services into the async socket sender."""
        stale: list[WebSocket] = []
        for websocket in self.connections.get(recipient_user_id, set()).copy():
            try:
                anyio.from_thread.run(websocket.send_json, payload)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)

    def clear(self) -> None:
        """Reset test-time connection state between isolated app runs."""
        self.connections.clear()


manager = NotificationConnectionManager()
set_notification_event_publisher(manager.publish_from_sync)


def current_user_from_websocket(websocket: WebSocket, db: Session, settings: Settings) -> User:
    """Resolve notification WebSocket auth from the existing access-token cookie."""
    access_token = websocket.cookies.get(settings.access_token_cookie_name)
    if access_token is None:
        raise APIError(401, "not_authenticated", "Authentication is required.")
    user_id = decode_token(access_token, "access", settings)
    if user_id is None:
        raise APIError(401, "not_authenticated", "Authentication is required.")
    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise APIError(401, "not_authenticated", "Authentication is required.")
    return user


@router.get("", response_model=NotificationListResponse)
def list_notifications(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    unread: bool | None = None,
) -> NotificationListResponse:
    """List notifications owned by the current authenticated user."""
    notifications, total = NotificationService(db).list_notifications(
        current_user, limit, offset, unread
    )
    return NotificationListResponse(
        items=[NotificationRead.model_validate(notification) for notification in notifications],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def get_unread_count(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationUnreadCountResponse:
    """Return the current user's unread notification count."""
    return NotificationUnreadCountResponse(
        unread_count=NotificationService(db).unread_count(current_user)
    )


@router.patch("/{notification_id}", response_model=NotificationRead)
def update_notification(
    notification_id: uuid.UUID,
    payload: NotificationUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> NotificationRead:
    """Update one current-user notification read state."""
    notification = NotificationService(db).set_read_state(
        current_user, notification_id, read=payload.read
    )
    return NotificationRead.model_validate(notification)


@router.post("/mark-all-read", status_code=204)
def mark_all_read(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Mark all current-user notifications read."""
    NotificationService(db).mark_all_read(current_user)
    return Response(status_code=204)


@router.websocket("/ws")
async def notification_websocket(
    websocket: WebSocket,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Deliver current-user notification events over an authenticated WebSocket."""
    try:
        current_user = current_user_from_websocket(websocket, db, settings)
        await manager.connect(current_user.id, websocket)
    except APIError:
        await websocket.close(code=1008)
        return
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
