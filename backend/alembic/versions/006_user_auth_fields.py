"""User auth fields."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_user_auth_fields"
down_revision: Union[str, None] = "005_workout_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("hashed_password", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("users", "is_admin")
    op.drop_column("users", "is_active")
    op.drop_column("users", "hashed_password")
