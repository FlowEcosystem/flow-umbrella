"""Репозиторий agents-домена."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.agents.models import Agent, AgentOS, AgentStatus


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _active_agents(self) -> Select[tuple[Agent]]:
        return select(Agent).where(Agent.deleted_at.is_(None))

    async def get_by_id(self, agent_id: UUID) -> Agent | None:
        stmt = self._active_agents().where(Agent.id == agent_id)
        return await self._session.scalar(stmt)

    async def get_by_hostname(self, hostname: str) -> Agent | None:
        stmt = self._active_agents().where(Agent.hostname == hostname)
        return await self._session.scalar(stmt)

    async def get_by_enrollment_token_hash(self, token_hash: str) -> Agent | None:
        stmt = self._active_agents().where(
            Agent.enrollment_token_hash == token_hash
        )
        return await self._session.scalar(stmt)

    async def get_by_agent_token_hash(self, token_hash: str) -> Agent | None:
        stmt = self._active_agents().where(
            Agent.agent_token_hash == token_hash,
            Agent.status.in_([AgentStatus.ACTIVE, AgentStatus.DISABLED]),
        )
        return await self._session.scalar(stmt)

    async def mark_stale_offline(self, cutoff: datetime) -> int:
        """Переводит ACTIVE-агентов без heartbeat с момента cutoff в DISABLED.

        Возвращает количество затронутых строк.
        """
        stmt = (
            update(Agent)
            .where(
                Agent.status == AgentStatus.ACTIVE,
                Agent.last_seen_at.is_not(None),
                Agent.last_seen_at < cutoff,
                Agent.deleted_at.is_(None),
            )
            .values(status=AgentStatus.DISABLED)
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def create(
        self,
        *,
        hostname: str,
        os: AgentOS,
        status: AgentStatus,
        enrollment_token_hash: str,
        enrollment_token_expires_at: datetime,
        notes: str | None = None,
    ) -> Agent:
        agent = Agent(
            hostname=hostname,
            os=os,
            status=status,
            enrollment_token_hash=enrollment_token_hash,
            enrollment_token_expires_at=enrollment_token_expires_at,
            notes=notes,
        )
        self._session.add(agent)
        await self._session.flush()
        return agent

    async def update(self, agent: Agent, fields: dict) -> Agent:
        for key, value in fields.items():
            setattr(agent, key, value)
        await self._session.flush()
        return agent

    async def soft_delete(self, agent: Agent) -> None:
        agent.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def list_filtered(
        self,
        *,
        limit: int,
        offset: int,
        statuses: list[AgentStatus] | None = None,
        os: AgentOS | None = None,
        search: str | None = None,
    ) -> list[Agent]:
        stmt = self._active_agents()
        stmt = self._apply_filters(stmt, statuses, os, search)
        stmt = stmt.order_by(Agent.created_at.desc()).limit(limit).offset(offset)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def count_filtered(
        self,
        *,
        statuses: list[AgentStatus] | None = None,
        os: AgentOS | None = None,
        search: str | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(Agent)
            .where(Agent.deleted_at.is_(None))
        )
        stmt = self._apply_filters(stmt, statuses, os, search)
        return await self._session.scalar(stmt) or 0

    @staticmethod
    def _apply_filters(
        stmt,
        statuses: list[AgentStatus] | None,
        os: AgentOS | None,
        search: str | None,
    ):
        if statuses:
            stmt = stmt.where(Agent.status.in_(statuses))
        if os is not None:
            stmt = stmt.where(Agent.os == os)
        if search:
            # ILIKE — PostgreSQL'евский case-insensitive поиск.
            # %s% — частичное совпадение. Санитайзинг не нужен —
            # SQLAlchemy экранирует параметр.
            stmt = stmt.where(Agent.hostname.ilike(f"%{search}%"))
        return stmt