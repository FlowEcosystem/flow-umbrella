"""Декларативная база для всех моделей.

Экспортирует:
- Base: базовый класс для всех ORM-моделей
- UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin: переиспользуемые миксины

Правила:
- Все модели наследуются от Base и нужных миксинов.
- Имя таблицы задаётся через __tablename__, в snake_case, во множественном числе:
  class Agent(Base, ...) → __tablename__ = "agents"
- Метаданные (MetaData) используют naming convention — Alembic будет генерить
  консистентные имена констрейнтов.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, MetaData, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


# Конвенция именования констрейнтов. Alembic использует её при autogenerate.
# Без этого PostgreSQL даст имена типа "agents_hostname_key", которые
# Alembic не сможет корректно откатить в downgrade().
# Форматы:
#   ix  — index
#   uq  — unique constraint
#   ck  — check constraint
#   fk  — foreign key
#   pk  — primary key
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    # Красивый repr для отладки: Agent(id=abc-123, hostname='laptop-01')
    def __repr__(self) -> str:
        attrs: list[str] = []
        for column in self.__table__.primary_key.columns: # pyright: ignore[reportAttributeAccessIssue]
            value = getattr(self, column.name, None)
            attrs.append(f"{column.name}={value!r}")
        return f"{self.__class__.__name__}({', '.join(attrs)})"


class UUIDPrimaryKeyMixin:
    """Первичный ключ UUID v4.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )


class TimestampMixin:
    """Автоматические created_at и updated_at.

    Оба в UTC, timezone-aware. В PostgreSQL хранятся как TIMESTAMPTZ.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        # onupdate срабатывает при любом UPDATE — ORM сам подставит now().
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )


class SoftDeleteMixin:
    """Soft-delete: ставим deleted_at вместо физического удаления.
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=None,
        nullable=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None