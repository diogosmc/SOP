"""Finance transactions table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_finance_transactions"
down_revision: Union[str, None] = "002_main_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    finance_transaction_type = postgresql.ENUM(
        "income", "expense", name="finance_transaction_type", create_type=True
    )

    op.create_table(
        "finance_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("type", finance_transaction_type, nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_finance_transactions_user_id", "finance_transactions", ["user_id"])
    op.create_index("ix_finance_transactions_type", "finance_transactions", ["type"])
    op.create_index("ix_finance_transactions_category", "finance_transactions", ["category"])
    op.create_index(
        "ix_finance_transactions_transaction_date", "finance_transactions", ["transaction_date"]
    )


def downgrade() -> None:
    op.drop_index("ix_finance_transactions_transaction_date", table_name="finance_transactions")
    op.drop_index("ix_finance_transactions_category", table_name="finance_transactions")
    op.drop_index("ix_finance_transactions_type", table_name="finance_transactions")
    op.drop_index("ix_finance_transactions_user_id", table_name="finance_transactions")
    op.drop_table("finance_transactions")
    op.execute("DROP TYPE IF EXISTS finance_transaction_type")
