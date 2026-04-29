"""Репозиторий процессов агентов."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, desc, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.processes.models import AgentProcessSnapshot, AgentProcessStat
from umbrella_server.domains.processes.schemas import AgentProcessPush


class ProcessRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def insert_snapshot(
        self, agent_id: UUID, payload: AgentProcessPush
    ) -> AgentProcessSnapshot:
        snap = AgentProcessSnapshot(
            agent_id=agent_id,
            collected_at=payload.collected_at,
            processes=[p.model_dump() for p in payload.processes],
        )
        self._session.add(snap)
        await self._session.flush()
        return snap

    async def upsert_stats(self, agent_id: UUID, payload: AgentProcessPush) -> None:
        now = payload.collected_at
        for proc in payload.processes:
            stmt = (
                pg_insert(AgentProcessStat)
                .values(
                    agent_id=agent_id,
                    process_name=proc.name,
                    seen_count=1,
                    first_seen_at=now,
                    last_seen_at=now,
                )
                .on_conflict_do_update(
                    index_elements=["agent_id", "process_name"],
                    set_=dict(
                        seen_count=AgentProcessStat.seen_count + 1,
                        last_seen_at=now,
                    ),
                )
            )
            await self._session.execute(stmt)

    async def get_latest_snapshot(self, agent_id: UUID) -> AgentProcessSnapshot | None:
        stmt = (
            select(AgentProcessSnapshot)
            .where(AgentProcessSnapshot.agent_id == agent_id)
            .order_by(AgentProcessSnapshot.collected_at.desc())
            .limit(1)
        )
        return await self._session.scalar(stmt)

    async def get_stats(
        self, agent_id: UUID, limit: int = 20
    ) -> list[AgentProcessStat]:
        stmt = (
            select(AgentProcessStat)
            .where(AgentProcessStat.agent_id == agent_id)
            .order_by(AgentProcessStat.seen_count.desc())
            .limit(limit)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_global_stats(self, limit: int = 20) -> list[dict]:
        stmt = (
            select(
                AgentProcessStat.process_name,
                func.sum(AgentProcessStat.seen_count).label("total_seen"),
                func.count(AgentProcessStat.agent_id.distinct()).label("agent_count"),
            )
            .group_by(AgentProcessStat.process_name)
            .order_by(desc("total_seen"))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [
            {
                "process_name": row.process_name,
                "total_seen": row.total_seen,
                "agent_count": row.agent_count,
            }
            for row in result.all()
        ]

    async def delete_old_snapshots(self, agent_id: UUID, cutoff: datetime) -> int:
        stmt = delete(AgentProcessSnapshot).where(
            AgentProcessSnapshot.agent_id == agent_id,
            AgentProcessSnapshot.collected_at < cutoff,
        )
        result = await self._session.execute(stmt)
        return result.rowcount
