"""Модель Agent и связанные enum'ы."""

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from umbrella_server.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from umbrella_server.domains.groups.models import Group


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    DECOMMISSIONED = "decommissioned"


class AgentOS(str, enum.Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class EnrollmentToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Одноразовый токен для self-enrollment агента.

    Не привязан к конкретному агенту до момента использования.
    Агент сам создаёт свою запись при enrollment.
    """
    __tablename__ = "enrollment_tokens"

    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Опциональные метаданные для администратора.
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Максимальное количество использований (NULL = одноразовый).
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uses_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    # В какую группу автоматически добавить агента при enrollment.
    group_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Заполняется при использовании токена.
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    used_by_agent_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_by_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("admins.id", ondelete="SET NULL"),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_enrollment_tokens_token_hash", "token_hash"),
    )

    @property
    def is_exhausted(self) -> bool:
        """Токен исчерпан: одноразовый и уже использован, или достигнут лимит uses."""
        if self.max_uses is None:
            return self.used_at is not None
        return self.uses_count >= self.max_uses


class Agent(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "agents"

    # Заполняется агентом при enrollment (до этого NULL).
    hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agent_status", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AgentStatus.ACTIVE,
    )
    os: Mapped[AgentOS | None] = mapped_column(
        Enum(AgentOS, name="agent_os", native_enum=True, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    os_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    enrolled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Заполняется после enrollment.
    agent_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cert_serial: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cert_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    groups: Mapped[list["Group"]] = relationship(
        secondary="agent_group_memberships",
        back_populates="agents",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_agents_agent_token_hash", "agent_token_hash"),
        Index("ix_agents_status", "status"),
    )
