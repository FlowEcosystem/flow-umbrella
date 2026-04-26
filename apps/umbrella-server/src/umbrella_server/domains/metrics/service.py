"""Сервис метрик агентов."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.agents.models import Agent
from umbrella_server.domains.metrics.models import AgentMetric
from umbrella_server.domains.metrics.repository import MetricsRepository
from umbrella_server.domains.metrics.schemas import AgentMetricPush

# Хранить метрики за последние 24 часа.
_RETENTION_HOURS = 24


class MetricsService:
    def __init__(self, session: AsyncSession, repo: MetricsRepository) -> None:
        self._session = session
        self._repo = repo

    async def push(self, agent: Agent, payload: AgentMetricPush) -> AgentMetric:
        metric = await self._repo.insert(agent.id, payload)
        cutoff = datetime.now(UTC) - timedelta(hours=_RETENTION_HOURS)
        await self._repo.delete_old(agent.id, cutoff)
        await self._session.commit()
        return metric

    async def get_history(self, agent_id: UUID, limit: int = 60) -> list[AgentMetric]:
        return await self._repo.get_history(agent_id, limit)
