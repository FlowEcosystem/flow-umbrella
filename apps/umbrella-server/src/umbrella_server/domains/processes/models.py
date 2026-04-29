"""ORM-модели для снимков и статистики процессов агентов."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from umbrella_server.db.base import Base, UUIDPrimaryKeyMixin


class AgentProcessSnapshot(Base, UUIDPrimaryKeyMixin):
    """Снимок списка процессов в момент времени."""

    __tablename__ = "agent_process_snapshots"

    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    # Массив объектов: [{name, pid, cpu_percent, mem_mb}, ...]
    processes: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    __table_args__ = (
        Index("ix_agent_process_snapshots_agent_collected", "agent_id", "collected_at"),
    )


class AgentProcessStat(Base):
    """Накопленная статистика появлений процесса на агенте."""

    __tablename__ = "agent_process_stats"

    agent_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        primary_key=True,
    )
    process_name: Mapped[str] = mapped_column(
        String(255), nullable=False, primary_key=True
    )
    # Сколько раз этот процесс присутствовал в пуше
    seen_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    __table_args__ = (
        Index("ix_agent_process_stats_agent_count", "agent_id", "seen_count"),
    )
