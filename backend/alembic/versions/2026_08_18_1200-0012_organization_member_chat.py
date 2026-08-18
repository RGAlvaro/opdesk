"""Add organization member chat persistence.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-18 12:00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create chat conversations, participants, messages, and read state."""
    op.execute("ALTER TYPE notification_type ADD VALUE IF NOT EXISTS 'chat.unread'")
    chat_conversation_type = postgresql.ENUM(
        "direct",
        "organization_channel",
        "project_channel",
        name="chat_conversation_type",
        create_type=False,
    )
    chat_conversation_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "chat_conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("conversation_type", chat_conversation_type, nullable=False),
        sa.Column("project_id", sa.Uuid(), nullable=True),
        sa.Column("direct_key", sa.String(length=80), nullable=True),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chat_conversations_organization_id", "chat_conversations", ["organization_id"]
    )
    op.create_index("ix_chat_conversations_project_id", "chat_conversations", ["project_id"])
    op.create_index("ix_chat_conversations_type", "chat_conversations", ["conversation_type"])
    op.create_index(
        "uq_chat_organization_channel",
        "chat_conversations",
        ["organization_id"],
        unique=True,
        postgresql_where=sa.text("conversation_type = 'organization_channel'"),
    )
    op.create_index(
        "uq_chat_project_channel",
        "chat_conversations",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("conversation_type = 'project_channel'"),
    )
    op.create_index(
        "uq_chat_direct_pair",
        "chat_conversations",
        ["organization_id", "direct_key"],
        unique=True,
        postgresql_where=sa.text("conversation_type = 'direct'"),
    )

    op.create_table(
        "chat_conversation_participants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["chat_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "conversation_id",
            "user_id",
            name="uq_chat_participant_conversation_user",
        ),
    )
    op.create_index("ix_chat_participants_user_id", "chat_conversation_participants", ["user_id"])
    op.create_index(
        "ix_chat_participants_organization_user",
        "chat_conversation_participants",
        ["organization_id", "user_id"],
    )

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("sender_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["chat_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_chat_messages_conversation_created",
        "chat_messages",
        ["conversation_id", "created_at"],
    )
    op.create_index("ix_chat_messages_organization_id", "chat_messages", ["organization_id"])
    op.create_index("ix_chat_messages_sender_id", "chat_messages", ["sender_id"])

    op.create_table(
        "chat_conversation_reads",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["conversation_id"], ["chat_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conversation_id", "user_id", name="uq_chat_read_conversation_user"),
    )
    op.create_index("ix_chat_reads_user_id", "chat_conversation_reads", ["user_id"])


def downgrade() -> None:
    """Remove organization chat persistence."""
    op.drop_index("ix_chat_reads_user_id", table_name="chat_conversation_reads")
    op.drop_table("chat_conversation_reads")
    op.drop_index("ix_chat_messages_sender_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_organization_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_conversation_created", table_name="chat_messages")
    op.drop_table("chat_messages")
    op.drop_index(
        "ix_chat_participants_organization_user", table_name="chat_conversation_participants"
    )
    op.drop_index("ix_chat_participants_user_id", table_name="chat_conversation_participants")
    op.drop_table("chat_conversation_participants")
    op.drop_index("uq_chat_direct_pair", table_name="chat_conversations")
    op.drop_index("uq_chat_project_channel", table_name="chat_conversations")
    op.drop_index("uq_chat_organization_channel", table_name="chat_conversations")
    op.drop_index("ix_chat_conversations_type", table_name="chat_conversations")
    op.drop_index("ix_chat_conversations_project_id", table_name="chat_conversations")
    op.drop_index("ix_chat_conversations_organization_id", table_name="chat_conversations")
    op.drop_table("chat_conversations")
    chat_conversation_type = postgresql.ENUM(
        "direct", "organization_channel", "project_channel", name="chat_conversation_type"
    )
    chat_conversation_type.drop(op.get_bind(), checkfirst=True)
