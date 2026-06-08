"""Reminder model."""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.modules.users.models import User


class ReminderChannel(str, enum.Enum):
    TELEGRAM = "telegram"
    DASHBOARD = "dashboard"
    BOTH = "both"


class ReminderStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


class Reminder(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reminders"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remind_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    recurrence_rule: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    channel: Mapped[ReminderChannel] = mapped_column(
        Enum(
            ReminderChannel,
            name="reminder_channel",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=ReminderChannel.BOTH,
        nullable=False,
    )
    status: Mapped[ReminderStatus] = mapped_column(
        Enum(
            ReminderStatus,
            name="reminder_status",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=ReminderStatus.PENDING,
        index=True,
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="reminders")
