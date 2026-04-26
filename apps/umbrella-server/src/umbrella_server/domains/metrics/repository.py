"""Репозиторий метрик агентов."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.metrics.models import AgentMetric
from umbrella_server.domains.metrics.schemas import AgentMetricPush


class MetricsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert(self, agent_id: UUID, payload: AgentMetricPush) -> AgentMetric:
        metric = AgentMetric(
            agent_id=agent_id,
            collected_at=payload.collected_at,
            cpu_percent=payload.cpu_percent,
            ram_used_mb=payload.ram_used_mb,
            ram_total_mb=payload.ram_total_mb,
            disk_used_gb=payload.disk_used_gb,
            disk_total_gb=payload.disk_total_gb,
        )
        self._session.add(metric)
        await self._session.flush()
        return metric

    async def get_history(self, agent_id: UUID, limit: int = 60) -> list[AgentMetric]:
        stmt = (
            select(AgentMetric)
            .where(AgentMetric.agent_id == agent_id)
            .order_by(AgentMetric.collected_at.desc())
            .limit(limit)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def delete_old(self, agent_id: UUID, cutoff: datetime) -> int:
        stmt = delete(AgentMetric).where(
            AgentMetric.agent_id == agent_id,
            AgentMetric.collected_at < cutoff,
        )
        result = await self._session.execute(stmt)
        return result.rowcount
