"""HTTP and WebSocket endpoints for internal organization chat."""

import uuid
from collections import defaultdict
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.api.errors import APIError
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models.chat import ChatConversation, ChatMessage
from app.models.user import User, UserAccountType
from app.repositories.users import UserRepository
from app.schemas.chat import (
    ChatConversationListResponse,
    ChatConversationRead,
    ChatDirectConversationCreateRequest,
    ChatMemberListResponse,
    ChatMemberRead,
    ChatMessageCreateRequest,
    ChatMessageListResponse,
    ChatMessageRead,
    ChatWebSocketSend,
)
from app.services.chat import ChatService
from app.services.security import decode_token

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatConnectionManager:
    """Track in-process chat WebSocket connections by conversation."""

    def __init__(self) -> None:
        """Create an empty connection registry."""
        self.connections: dict[uuid.UUID, set[WebSocket]] = defaultdict(set)

    async def connect(self, websocket: WebSocket) -> None:
        """Accept one authenticated WebSocket connection."""
        await websocket.accept()

    def subscribe(self, conversation_id: uuid.UUID, websocket: WebSocket) -> None:
        """Register a socket for a conversation after authorization succeeds."""
        self.connections[conversation_id].add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a socket from every in-process subscription set."""
        for conversation_id in list(self.connections):
            sockets = self.connections[conversation_id]
            sockets.discard(websocket)
            if not sockets:
                del self.connections[conversation_id]

    async def broadcast(self, conversation_id: uuid.UUID, payload: dict[str, Any]) -> None:
        """Send one JSON event to currently subscribed sockets."""
        stale: list[WebSocket] = []
        for websocket in self.connections.get(conversation_id, set()).copy():
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(websocket)


manager = ChatConnectionManager()


def message_read(message: ChatMessage) -> ChatMessageRead:
    """Convert a persisted chat message into its public shape."""
    return ChatMessageRead.model_validate(message)


def conversation_read(service: ChatService, conversation: ChatConversation) -> ChatConversationRead:
    """Convert a conversation into a public response with direct target metadata."""
    participant_ids = service.chat.list_participant_user_ids(conversation.id)
    direct_user_id = None
    if conversation.conversation_type.value == "direct":
        direct_candidates = [user_id for user_id in participant_ids]
        direct_user_id = direct_candidates[0] if len(direct_candidates) == 1 else None
    return ChatConversationRead(
        id=conversation.id,
        organization_id=conversation.organization_id,
        conversation_type=conversation.conversation_type,
        project_id=conversation.project_id,
        direct_user_id=direct_user_id,
        unread_count=0,
        last_message=None,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def conversation_summary_read(
    actor: User,
    conversation: ChatConversation,
    last_message: ChatMessage | None,
    unread_count: int,
    service: ChatService,
) -> ChatConversationRead:
    """Convert a listed conversation into the current-user summary shape."""
    participant_ids = service.chat.list_participant_user_ids(conversation.id)
    direct_user_id = None
    if conversation.conversation_type.value == "direct":
        direct_user_id = next((user_id for user_id in participant_ids if user_id != actor.id), None)
    return ChatConversationRead(
        id=conversation.id,
        organization_id=conversation.organization_id,
        conversation_type=conversation.conversation_type,
        project_id=conversation.project_id,
        direct_user_id=direct_user_id,
        unread_count=unread_count,
        last_message=message_read(last_message) if last_message is not None else None,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
    )


def current_user_from_websocket(websocket: WebSocket, db: Session, settings: Settings) -> User:
    """Resolve WebSocket authentication from the existing access-token cookie."""
    access_token = websocket.cookies.get(settings.access_token_cookie_name)
    if access_token is None:
        raise APIError(401, "not_authenticated", "Authentication is required.")
    user_id = decode_token(access_token, "access", settings)
    if user_id is None:
        raise APIError(401, "not_authenticated", "Authentication is required.")
    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise APIError(401, "not_authenticated", "Authentication is required.")
    if user.account_type == UserAccountType.CLIENT:
        raise APIError(403, "internal_member_required", "Internal membership is required.")
    return user


@router.get("/organizations/{organization_id}/chat/members", response_model=ChatMemberListResponse)
def list_chat_members(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatMemberListResponse:
    """List internal organization members ordered for chat discovery."""
    rows = ChatService(db).list_members(current_user, organization_id)
    return ChatMemberListResponse(
        items=[
            ChatMemberRead(
                user_id=user.id,
                full_name=user.full_name,
                email=user.email,
                role=membership.role,
                shares_project=shares_project,
            )
            for membership, user, shares_project in rows
        ]
    )


@router.get(
    "/organizations/{organization_id}/chat/conversations",
    response_model=ChatConversationListResponse,
)
def list_chat_conversations(
    organization_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatConversationListResponse:
    """List current-user conversations inside an organization."""
    service = ChatService(db)
    rows = service.list_conversations(current_user, organization_id)
    return ChatConversationListResponse(
        items=[
            conversation_summary_read(
                current_user,
                conversation,
                last_message,
                unread_count,
                service,
            )
            for conversation, _participant, last_message, unread_count in rows
        ]
    )


@router.post(
    "/organizations/{organization_id}/chat/direct-conversations",
    response_model=ChatConversationRead,
    status_code=201,
)
def create_direct_conversation(
    organization_id: uuid.UUID,
    payload: ChatDirectConversationCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatConversationRead:
    """Create or return a direct chat conversation."""
    service = ChatService(db)
    conversation = service.create_direct_conversation(
        current_user, organization_id, payload.target_user_id
    )
    participant_ids = service.chat.list_participant_user_ids(conversation.id)
    target_user_id = next(
        (user_id for user_id in participant_ids if user_id != current_user.id),
        None,
    )
    response = conversation_read(service, conversation)
    response.direct_user_id = target_user_id
    return response


@router.get("/projects/{project_id}/chat/channel", response_model=ChatConversationRead)
def get_project_chat_channel(
    project_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatConversationRead:
    """Create or return one project channel for authorized participants."""
    service = ChatService(db)
    conversation = service.get_project_channel(current_user, project_id)
    return conversation_read(service, conversation)


@router.get(
    "/chat/conversations/{conversation_id}/messages", response_model=ChatMessageListResponse
)
def list_chat_messages(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ChatMessageListResponse:
    """List chat history visible to the current participant."""
    messages, total = ChatService(db).list_messages(current_user, conversation_id, limit, offset)
    return ChatMessageListResponse(
        items=[message_read(message) for message in messages],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/chat/conversations/{conversation_id}/messages",
    response_model=ChatMessageRead,
    status_code=201,
)
async def create_chat_message(
    conversation_id: uuid.UUID,
    payload: ChatMessageCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatMessageRead:
    """Persist one chat message and fan it out to connected subscribers."""
    message = ChatService(db).send_message(current_user, conversation_id, payload.body)
    event = {"type": "message.created", "message": message_read(message).model_dump(mode="json")}
    await manager.broadcast(conversation_id, event)
    return message_read(message)


@router.post("/chat/conversations/{conversation_id}/read", response_model=ChatConversationRead)
def mark_chat_conversation_read(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatConversationRead:
    """Mark one conversation read for the current user."""
    service = ChatService(db)
    conversation = service.mark_read(current_user, conversation_id)
    return conversation_read(service, conversation)


@router.post("/chat/conversations/{conversation_id}/clear", response_model=ChatConversationRead)
def clear_chat_conversation(
    conversation_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ChatConversationRead:
    """Clear one conversation from the current user's chat view."""
    service = ChatService(db)
    conversation = service.clear_conversation(current_user, conversation_id)
    return conversation_read(service, conversation)


@router.websocket("/chat/ws")
async def chat_websocket(
    websocket: WebSocket,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Receive and deliver chat messages over an authenticated WebSocket."""
    try:
        current_user = current_user_from_websocket(websocket, db, settings)
        await manager.connect(websocket)
    except APIError:
        await websocket.close(code=1008)
        return
    service = ChatService(db)
    try:
        while True:
            payload = await websocket.receive_json()
            if payload.get("type") == "subscribe":
                conversation_id = uuid.UUID(str(payload.get("conversation_id")))
                service.list_messages(current_user, conversation_id, 1, 0)
                manager.subscribe(conversation_id, websocket)
                await websocket.send_json(
                    {"type": "subscribed", "conversation_id": str(conversation_id)}
                )
                continue
            if payload.get("type") != "message.send":
                await websocket.send_json(
                    {"type": "error", "code": "invalid_message", "message": "Unsupported event."}
                )
                continue
            try:
                data = ChatWebSocketSend.model_validate(payload)
                message = service.send_message(current_user, data.conversation_id, data.body)
                event = {
                    "type": "message.created",
                    "message": message_read(message).model_dump(mode="json"),
                }
                await manager.broadcast(data.conversation_id, event)
            except (APIError, ValidationError, ValueError) as exc:
                code = exc.code if isinstance(exc, APIError) else "invalid_message"
                await websocket.send_json(
                    {"type": "error", "code": code, "message": "Message was not accepted."}
                )
    except WebSocketDisconnect:
        manager.disconnect(websocket)
