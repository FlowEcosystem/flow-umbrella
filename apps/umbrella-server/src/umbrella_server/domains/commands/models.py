"""Модели домена команд."""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, JSON, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from umbrella_server.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CommandType(str, enum.Enum):
    REBOOT = "reboot"
    COLLECT_DIAGNOSTICS = "collect_diagnostics"
    UPDATE_SELF = "update_self"
    APPLY_CONFIG = "apply_config"


class CommandStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    ACKNOWLEDGED = "acknowledged"
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"


class Command(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "commands"

    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[CommandType] = mapped_column(
        Enum(CommandType, name="command_type", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[CommandStatus] = mapped_column(
        Enum(CommandStatus, name="command_status", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CommandStatus.PENDING,
    )

    # Произвольные параметры команды (например, версия для update_self).
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Ответ агента после выполнения.
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    issued_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("admins.id", ondelete="SET NULL"), nullable=True
    )

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # После этого момента агент не должен исполнять команду.
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_commands_agent_id", "agent_id"),
        Index("ix_commands_status", "status"),
    )
