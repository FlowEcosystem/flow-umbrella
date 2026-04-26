"""Модель метрик агентов."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, Index, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from umbrella_server.db.base import Base, UUIDPrimaryKeyMixin


class AgentMetric(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "agent_metrics"

    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    cpu_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    ram_used_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ram_total_mb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    disk_used_gb: Mapped[float | None] = mapped_column(Float, nullable=True)
    disk_total_gb: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_agent_metrics_agent_collected", "agent_id", "collected_at"),
    )
