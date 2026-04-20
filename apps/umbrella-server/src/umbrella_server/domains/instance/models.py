"""Модель BranchConfig — идентичность конкретного сервера филиала.

Таблица всегда содержит ровно одну строку (id=1). Запись создаётся
автоматически при первом старте приложения через bootstrap.ensure_instance().
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from umbrella_server.db.base import Base, TimestampMixin


class BranchConfig(Base, TimestampMixin):
    __tablename__ = "branch_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    branch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, unique=True, nullable=False, default=uuid.uuid4
    )
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)

    hq_base_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    hq_enrollment_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    hq_access_token: Mapped[str | None] = mapped_column(String(512), nullable=True)
    hq_last_sync_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hq_sync_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        CheckConstraint("id = 1", name="ck_branch_config_singleton"),
    )