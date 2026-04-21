"""Модель Agent и связанные enum'ы."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from umbrella_server.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from umbrella_server.domains.groups.models import Group


class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DISABLED = "disabled"
    DECOMMISSIONED = "decommissioned"


class AgentOS(str, enum.Enum):
    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class Agent(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "agents"

    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agent_status", native_enum=True),
        nullable=False,
        default=AgentStatus.PENDING,
    )
    os: Mapped[AgentOS] = mapped_column(
        Enum(AgentOS, name="agent_os", native_enum=True),
        nullable=False,
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

    # Enrollment-токен: raw показывается админу один раз при создании/регенерации,
    # в БД только SHA-256 хэш.
    enrollment_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    enrollment_token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    groups: Mapped[list["Group"]] = relationship(  # noqa: F821
        secondary="agent_group_memberships",
        back_populates="agents",
        lazy="selectin",
    )


    __table_args__ = (
        # UNIQUE hostname только среди активных — позволяет пересоздать
        # агента с тем же hostname после soft-delete.
        Index(
            "uq_agents_hostname_active",
            "hostname",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
        # Быстрый поиск по hash при enrollment'е агента.
        Index("ix_agents_enrollment_token_hash", "enrollment_token_hash"),
        # Для фильтров в list-endpoint'е — частый предикат.
        Index("ix_agents_status", "status"),
    )