"""Initial schema — creates all tables from SQLAlchemy metadata."""

from typing import Sequence, Union

from alembic import op

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from app.db.base import Base
    from app.db import models  # noqa: F401

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    bind = op.get_bind()
    Base.metadata.create_all(bind)


def downgrade() -> None:
    from app.db.base import Base
    from app.db import models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.drop_all(bind)
