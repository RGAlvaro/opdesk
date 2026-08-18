"""Pydantic contracts for internal organization chat APIs."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.chat import ChatConversationType
from app.models.organization import MembershipRole


class ChatMemberRead(BaseModel):
    """Public organization member entry for the chat people list."""

    user_id: uuid.UUID
    full_name: str
    email: str
    role: MembershipRole
    shares_project: bool


class ChatMemberListResponse(BaseModel):
    """List of internal members visible in organization chat."""

    items: list[ChatMemberRead]


class ChatDirectConversationCreateRequest(BaseModel):
    """Request body for creating or retrieving a direct conversation."""

    target_user_id: uuid.UUID


class ChatMessageCreateRequest(BaseModel):
    """Request body for persisting one chat message."""

    body: str


class ChatMessageRead(BaseModel):
    """Public representation of one persisted chat message."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    conversation_id: uuid.UUID
    organization_id: uuid.UUID
    sender_id: uuid.UUID
    body: str
    created_at: datetime


class ChatConversationRead(BaseModel):
    """Public representation of a conversation visible to one participant."""

    id: uuid.UUID
    organization_id: uuid.UUID
    conversation_type: ChatConversationType
    project_id: uuid.UUID | None
    direct_user_id: uuid.UUID | None
    unread_count: int
    last_message: ChatMessageRead | None
    created_at: datetime
    updated_at: datetime


class ChatConversationListResponse(BaseModel):
    """List of current-user conversations inside one organization."""

    items: list[ChatConversationRead]


class ChatMessageListResponse(BaseModel):
    """Paginated chat message history response."""

    items: list[ChatMessageRead]
    total: int
    limit: int
    offset: int


class ChatWebSocketSend(BaseModel):
    """Message accepted over the chat WebSocket."""

    conversation_id: uuid.UUID
    body: str = Field(min_length=1, max_length=4000)
