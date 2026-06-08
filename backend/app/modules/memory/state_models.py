"""User conversation state model."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.users.models import User


class UserState(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_state"
    __table_args__ = (UniqueConstraint("user_id", name="uq_user_state_user_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mood: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    energy: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    current_focus: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    current_topic: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    conversation_mode: Mapped[str] = mapped_column(
        String(64), nullable=False, default="normal", server_default="normal"
    )
    last_intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    last_user_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_assistant_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    state_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    user: Mapped["User"] = relationship(back_populates="user_state")
