"""Database base and model tests."""

import uuid

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utc_now
from app.modules.users.models import User


def test_import_base() -> None:
    assert Base is not None
    assert hasattr(Base, "metadata")


def test_mixins_are_defined() -> None:
    assert TimestampMixin.created_at is not None
    assert TimestampMixin.updated_at is not None
    assert UUIDPrimaryKeyMixin.id is not None


def test_utc_now_returns_timezone_aware() -> None:
    now = utc_now()
    assert now.tzinfo is not None


def test_user_model_registered_on_metadata() -> None:
    assert "users" in Base.metadata.tables


def test_user_model_columns() -> None:
    table = User.__table__
    column_names = {column.name for column in table.columns}
    expected = {
        "id",
        "name",
        "email",
        "telegram_id",
        "timezone",
        "preferences",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(column_names)


def test_user_model_primary_key_is_uuid() -> None:
    pk = User.__table__.c.id
    assert pk.primary_key is True
    assert "UUID" in str(pk.type)
