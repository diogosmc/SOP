"""Add user_state table for Conversation Brain."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_user_state"
down_revision: Union[str, None] = "007_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_state",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mood", sa.String(64), nullable=True),
        sa.Column("energy", sa.String(64), nullable=True),
        sa.Column("current_focus", sa.String(255), nullable=True),
        sa.Column("current_topic", sa.String(128), nullable=True),
        sa.Column(
            "conversation_mode",
            sa.String(64),
            nullable=False,
            server_default="normal",
        ),
        sa.Column("last_intent", sa.String(64), nullable=True),
        sa.Column("last_user_message", sa.Text(), nullable=True),
        sa.Column("last_assistant_message", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", name="uq_user_state_user_id"),
    )
    op.create_index("ix_user_state_user_id", "user_state", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_user_state_user_id", table_name="user_state")
    op.drop_table("user_state")
