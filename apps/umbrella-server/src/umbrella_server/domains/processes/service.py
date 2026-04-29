"""Сервис процессов агентов."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.agents.models import Agent
from umbrella_server.domains.processes.models import AgentProcessSnapshot, AgentProcessStat
from umbrella_server.domains.processes.repository import ProcessRepository
from umbrella_server.domains.processes.schemas import AgentProcessPush

_RETENTION_HOURS = 24


class ProcessService:
    def __init__(self, session: AsyncSession, repo: ProcessRepository) -> None:
        self._session = session
        self._repo = repo

    async def push(self, agent: Agent, payload: AgentProcessPush) -> None:
        await self._repo.insert_snapshot(agent.id, payload)
        await self._repo.upsert_stats(agent.id, payload)
        cutoff = datetime.now(UTC) - timedelta(hours=_RETENTION_HOURS)
        await self._repo.delete_old_snapshots(agent.id, cutoff)
        await self._session.commit()

    async def get_latest(self, agent_id: UUID) -> AgentProcessSnapshot | None:
        return await self._repo.get_latest_snapshot(agent_id)

    async def get_stats(
        self, agent_id: UUID, limit: int = 20
    ) -> list[AgentProcessStat]:
        return await self._repo.get_stats(agent_id, limit)

    async def get_global_stats(self, limit: int = 20) -> list[dict]:
        return await self._repo.get_global_stats(limit)
