"""Data access operations for tenant-scoped chat conversations and messages."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chat import (
    ChatConversation,
    ChatConversationParticipant,
    ChatConversationRead,
    ChatConversationType,
    ChatMessage,
)
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import Project, ProjectMembership
from app.models.user import User, UserAccountType


class ChatRepository:
    """Keep chat queries scoped by organization, project, and participant."""

    def __init__(self, db: Session) -> None:
        """Store the active request transaction."""
        self.db = db

    def add_conversation(self, conversation: ChatConversation) -> ChatConversation:
        """Stage and flush a conversation row."""
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def add_participant(
        self, participant: ChatConversationParticipant
    ) -> ChatConversationParticipant:
        """Stage and flush one participant row."""
        self.db.add(participant)
        self.db.flush()
        return participant

    def add_read(self, read: ChatConversationRead) -> ChatConversationRead:
        """Stage and flush one read-state row."""
        self.db.add(read)
        self.db.flush()
        return read

    def add_message(self, message: ChatMessage) -> ChatMessage:
        """Stage and flush one persisted chat message."""
        self.db.add(message)
        self.db.flush()
        return message

    def list_internal_members(
        self, organization_id: uuid.UUID, actor_user_id: uuid.UUID
    ) -> list[tuple[OrganizationMembership, User, bool]]:
        """List organization members with shared-project grouping metadata."""
        shared_project_ids = (
            select(ProjectMembership.project_id)
            .join(Project, Project.id == ProjectMembership.project_id)
            .where(
                ProjectMembership.user_id == actor_user_id,
                Project.organization_id == organization_id,
                Project.is_archived.is_(False),
            )
        )
        shared_user_ids = (
            select(ProjectMembership.user_id)
            .where(
                ProjectMembership.organization_id == organization_id,
                ProjectMembership.project_id.in_(shared_project_ids),
                ProjectMembership.user_id != actor_user_id,
            )
            .distinct()
        )
        rows = self.db.execute(
            select(
                OrganizationMembership,
                User,
                User.id.in_(shared_user_ids).label("shares_project"),
            )
            .join(User, User.id == OrganizationMembership.user_id)
            .where(
                OrganizationMembership.organization_id == organization_id,
                User.account_type == UserAccountType.INTERNAL,
            )
            .order_by(
                User.id.in_(shared_user_ids).desc(),
                func.lower(User.full_name),
                func.lower(User.email),
                User.id,
            )
        ).all()
        return [(row[0], row[1], bool(row[2])) for row in rows]

    def get_organization_membership(
        self, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationMembership | None:
        """Return internal organization membership for one user."""
        return self.db.scalar(
            select(OrganizationMembership)
            .join(User, User.id == OrganizationMembership.user_id)
            .where(
                OrganizationMembership.organization_id == organization_id,
                OrganizationMembership.user_id == user_id,
                User.account_type == UserAccountType.INTERNAL,
            )
        )

    def get_project_for_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[Project, OrganizationMembership] | None:
        """Load a project when the actor belongs to its organization."""
        row = self.db.execute(
            select(Project, OrganizationMembership)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Project.organization_id,
            )
            .join(User, User.id == OrganizationMembership.user_id)
            .where(
                Project.id == project_id,
                OrganizationMembership.user_id == user_id,
                User.account_type == UserAccountType.INTERNAL,
            )
        ).one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    def get_project_membership(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> ProjectMembership | None:
        """Return explicit project access for a user."""
        return self.db.scalar(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.user_id == user_id,
            )
        )

    def list_project_participant_ids(self, project_id: uuid.UUID) -> list[uuid.UUID]:
        """Return internal users with explicit project participation."""
        return list(
            self.db.scalars(
                select(ProjectMembership.user_id)
                .join(User, User.id == ProjectMembership.user_id)
                .join(
                    OrganizationMembership,
                    (OrganizationMembership.organization_id == ProjectMembership.organization_id)
                    & (OrganizationMembership.user_id == ProjectMembership.user_id),
                )
                .where(
                    ProjectMembership.project_id == project_id,
                    User.account_type == UserAccountType.INTERNAL,
                )
                .order_by(ProjectMembership.created_at, ProjectMembership.id)
            )
        )

    def list_organization_participant_ids(self, organization_id: uuid.UUID) -> list[uuid.UUID]:
        """Return internal organization member IDs for organization channels."""
        return list(
            self.db.scalars(
                select(OrganizationMembership.user_id)
                .join(User, User.id == OrganizationMembership.user_id)
                .where(
                    OrganizationMembership.organization_id == organization_id,
                    User.account_type == UserAccountType.INTERNAL,
                )
                .order_by(OrganizationMembership.created_at, OrganizationMembership.id)
            )
        )

    def list_owner_admin_user_ids(self, organization_id: uuid.UUID) -> list[uuid.UUID]:
        """Return internal owner/admin user IDs with organization-wide project access."""
        return list(
            self.db.scalars(
                select(OrganizationMembership.user_id)
                .join(User, User.id == OrganizationMembership.user_id)
                .where(
                    OrganizationMembership.organization_id == organization_id,
                    OrganizationMembership.role.in_([MembershipRole.OWNER, MembershipRole.ADMIN]),
                    User.account_type == UserAccountType.INTERNAL,
                )
                .order_by(OrganizationMembership.created_at, OrganizationMembership.id)
            )
        )

    def get_direct_conversation(
        self, organization_id: uuid.UUID, direct_key: str
    ) -> ChatConversation | None:
        """Return an existing direct conversation by stable pair key."""
        return self.db.scalar(
            select(ChatConversation).where(
                ChatConversation.organization_id == organization_id,
                ChatConversation.conversation_type == ChatConversationType.DIRECT,
                ChatConversation.direct_key == direct_key,
            )
        )

    def get_organization_channel(self, organization_id: uuid.UUID) -> ChatConversation | None:
        """Return the singleton organization channel when present."""
        return self.db.scalar(
            select(ChatConversation).where(
                ChatConversation.organization_id == organization_id,
                ChatConversation.conversation_type == ChatConversationType.ORGANIZATION_CHANNEL,
            )
        )

    def get_project_channel(self, project_id: uuid.UUID) -> ChatConversation | None:
        """Return the singleton project channel when present."""
        return self.db.scalar(
            select(ChatConversation).where(
                ChatConversation.project_id == project_id,
                ChatConversation.conversation_type == ChatConversationType.PROJECT_CHANNEL,
            )
        )

    def get_conversation_for_participant(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[ChatConversation, ChatConversationParticipant] | None:
        """Load a conversation only when the user currently participates."""
        row = self.db.execute(
            select(ChatConversation, ChatConversationParticipant)
            .join(
                ChatConversationParticipant,
                ChatConversationParticipant.conversation_id == ChatConversation.id,
            )
            .where(
                ChatConversation.id == conversation_id,
                ChatConversationParticipant.user_id == user_id,
            )
        ).one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    def get_participant(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID
    ) -> ChatConversationParticipant | None:
        """Return one participant row when present."""
        return self.db.scalar(
            select(ChatConversationParticipant).where(
                ChatConversationParticipant.conversation_id == conversation_id,
                ChatConversationParticipant.user_id == user_id,
            )
        )

    def list_conversations_for_user(
        self, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[tuple[ChatConversation, ChatConversationParticipant, ChatMessage | None, int]]:
        """List visible conversations with last message and unread count."""
        rows = self.db.execute(
            select(ChatConversation, ChatConversationParticipant)
            .join(
                ChatConversationParticipant,
                ChatConversationParticipant.conversation_id == ChatConversation.id,
            )
            .where(
                ChatConversation.organization_id == organization_id,
                ChatConversationParticipant.user_id == user_id,
            )
            .order_by(ChatConversation.updated_at.desc(), ChatConversation.id.desc())
        ).all()
        items: list[
            tuple[ChatConversation, ChatConversationParticipant, ChatMessage | None, int]
        ] = []
        for conversation, participant in rows:
            last_message = self.db.scalar(
                select(ChatMessage)
                .where(
                    ChatMessage.conversation_id == conversation.id,
                    self._visible_after_clear_filter(participant),
                )
                .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
                .limit(1)
            )
            if participant.cleared_at is not None and last_message is None:
                continue
            unread_count = self.unread_count(conversation.id, user_id, participant.cleared_at)
            items.append((conversation, participant, last_message, unread_count))
        return items

    def list_messages(
        self,
        conversation_id: uuid.UUID,
        limit: int,
        offset: int,
        cleared_at: datetime | None,
    ) -> tuple[list[ChatMessage], int]:
        """List messages visible to one participant after personal clear state."""
        filters = [
            ChatMessage.conversation_id == conversation_id,
            self._after_clear_filter(cleared_at),
        ]
        total = self.db.scalar(select(func.count(ChatMessage.id)).where(*filters)) or 0
        messages = list(
            self.db.scalars(
                select(ChatMessage)
                .where(*filters)
                .order_by(ChatMessage.created_at, ChatMessage.id)
                .limit(limit)
                .offset(offset)
            )
        )
        return messages, total

    def unread_count(
        self, conversation_id: uuid.UUID, user_id: uuid.UUID, cleared_at: datetime | None
    ) -> int:
        """Count messages newer than the user's read marker and not sent by them."""
        read = self.db.scalar(
            select(ChatConversationRead).where(
                ChatConversationRead.conversation_id == conversation_id,
                ChatConversationRead.user_id == user_id,
            )
        )
        boundary = read.last_read_at if read is not None else None
        filters = [
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.sender_id != user_id,
            self._after_clear_filter(cleared_at),
        ]
        if boundary is not None:
            filters.append(ChatMessage.created_at > boundary)
        return self.db.scalar(select(func.count(ChatMessage.id)).where(*filters)) or 0

    def list_participant_user_ids(self, conversation_id: uuid.UUID) -> list[uuid.UUID]:
        """Return all participant IDs for delivery and notification fan-out."""
        return list(
            self.db.scalars(
                select(ChatConversationParticipant.user_id)
                .where(ChatConversationParticipant.conversation_id == conversation_id)
                .order_by(ChatConversationParticipant.created_at, ChatConversationParticipant.id)
            )
        )

    def mark_read(
        self,
        conversation: ChatConversation,
        user_id: uuid.UUID,
        read_at: datetime,
    ) -> ChatConversationRead:
        """Create or update one user's read marker for a conversation."""
        read = self.db.scalar(
            select(ChatConversationRead).where(
                ChatConversationRead.conversation_id == conversation.id,
                ChatConversationRead.user_id == user_id,
            )
        )
        if read is None:
            read = ChatConversationRead(
                conversation_id=conversation.id,
                organization_id=conversation.organization_id,
                user_id=user_id,
                last_read_at=read_at,
            )
            self.db.add(read)
        else:
            read.last_read_at = read_at
            self.db.add(read)
        self.db.flush()
        return read

    @staticmethod
    def _after_clear_filter(cleared_at: datetime | None) -> Any:
        """Build the SQL predicate for participant-specific message clearing."""
        if cleared_at is None:
            return ChatMessage.id.is_not(None)
        return ChatMessage.created_at > cleared_at

    @staticmethod
    def _visible_after_clear_filter(participant: ChatConversationParticipant) -> Any:
        """Build a message visibility predicate from one participant row."""
        if participant.cleared_at is None:
            return ChatMessage.id.is_not(None)
        return ChatMessage.created_at > participant.cleared_at
