"""Модели groups-домена: Group и association-таблица agent_group_memberships."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from umbrella_server.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


# Association-таблица (core, не ORM) — membership метаданные здесь.
# Cascade с обеих сторон: удалили агента или группу — membership исчезает.
agent_group_memberships = Table(
    "agent_group_memberships",
    Base.metadata,
    Column(
        "agent_id",
        ForeignKey("agents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "group_id",
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    ),
    Index("ix_agent_group_memberships_group_id", "group_id"),
)


class Group(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "groups"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Hex-цвет для UI-бейджа: "#4338ca"
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)

    # Связь many-to-many через association-таблицу.
    # "Agent" по строке — избегаем циклический импорт.
    agents: Mapped[list["Agent"]] = relationship(  # noqa: F821 # pyright: ignore[reportUndefinedVariable]
        secondary=agent_group_memberships,
        back_populates="groups",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "uq_groups_name_active",
            "name",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
    )