"""SQLAlchemy models for organization-scoped internal chat conversations."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.db.base import Base


class ChatConversationType(str, enum.Enum):
    """Supported conversation scopes for the first chat implementation."""

    DIRECT = "direct"
    ORGANIZATION_CHANNEL = "organization_channel"
    PROJECT_CHANNEL = "project_channel"


class ChatConversation(Base):
    """Persist one direct, organization, or project channel conversation."""

    __tablename__ = "chat_conversations"
    __table_args__ = (
        Index("ix_chat_conversations_organization_id", "organization_id"),
        Index("ix_chat_conversations_project_id", "project_id"),
        Index("ix_chat_conversations_type", "conversation_type"),
        Index(
            "uq_chat_organization_channel",
            "organization_id",
            unique=True,
            postgresql_where=text("conversation_type = 'organization_channel'"),
            sqlite_where=text("conversation_type = 'organization_channel'"),
        ),
        Index(
            "uq_chat_project_channel",
            "project_id",
            unique=True,
            postgresql_where=text("conversation_type = 'project_channel'"),
            sqlite_where=text("conversation_type = 'project_channel'"),
        ),
        Index(
            "uq_chat_direct_pair",
            "organization_id",
            "direct_key",
            unique=True,
            postgresql_where=text("conversation_type = 'direct'"),
            sqlite_where=text("conversation_type = 'direct'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    conversation_type: Mapped[ChatConversationType] = mapped_column(
        Enum(
            ChatConversationType,
            name="chat_conversation_type",
            values_callable=lambda values: [v.value for v in values],
        ),
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True
    )
    direct_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ChatConversationParticipant(Base):
    """Persist a user's participation and personal clear state in a conversation."""

    __tablename__ = "chat_conversation_participants"
    __table_args__ = (
        UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_chat_participant_conversation_user",
        ),
        Index("ix_chat_participants_user_id", "user_id"),
        Index("ix_chat_participants_organization_user", "organization_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ChatMessage(Base):
    """Persist one user-generated message after chat authorization succeeds."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_messages_conversation_created", "conversation_id", "created_at"),
        Index("ix_chat_messages_organization_id", "organization_id"),
        Index("ix_chat_messages_sender_id", "sender_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ChatConversationRead(Base):
    """Persist per-user read state used for unread conversation summaries."""

    __tablename__ = "chat_conversation_reads"
    __table_args__ = (
        UniqueConstraint("conversation_id", "user_id", name="uq_chat_read_conversation_user"),
        Index("ix_chat_reads_user_id", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
