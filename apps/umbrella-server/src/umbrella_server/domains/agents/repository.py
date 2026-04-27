"""Репозиторий agents-домена."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.agents.models import Agent, AgentOS, AgentStatus, EnrollmentToken
from umbrella_server.domains.groups.models import agent_group_memberships


class AgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── Enrollment tokens ────────────────────────────────────────────────────

    async def create_enrollment_token(
        self,
        *,
        token_hash: str,
        expires_at: datetime,
        note: str | None,
        group_id: UUID | None,
        max_uses: int | None,
        created_by_id: UUID | None,
    ) -> EnrollmentToken:
        token = EnrollmentToken(
            token_hash=token_hash,
            expires_at=expires_at,
            note=note,
            group_id=group_id,
            max_uses=max_uses,
            created_by_id=created_by_id,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_enrollment_token_by_hash(self, token_hash: str) -> EnrollmentToken | None:
        stmt = select(EnrollmentToken).where(EnrollmentToken.token_hash == token_hash)
        return await self._session.scalar(stmt)

    async def get_enrollment_token_by_id(self, token_id: UUID) -> EnrollmentToken | None:
        stmt = select(EnrollmentToken).where(EnrollmentToken.id == token_id)
        return await self._session.scalar(stmt)

    async def list_enrollment_tokens(self) -> list[EnrollmentToken]:
        stmt = select(EnrollmentToken).order_by(EnrollmentToken.created_at.desc())
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def update_enrollment_token(self, token: EnrollmentToken, fields: dict) -> None:
        for key, value in fields.items():
            setattr(token, key, value)
        await self._session.flush()

    async def delete_enrollment_token(self, token: EnrollmentToken) -> None:
        await self._session.delete(token)
        await self._session.flush()

    # ── Agents ───────────────────────────────────────────────────────────────

    def _active_agents(self) -> Select[tuple[Agent]]:
        return select(Agent).where(Agent.deleted_at.is_(None))

    async def get_by_id(self, agent_id: UUID) -> Agent | None:
        stmt = self._active_agents().where(Agent.id == agent_id)
        return await self._session.scalar(stmt)

    async def get_by_hostname(self, hostname: str) -> Agent | None:
        stmt = self._active_agents().where(Agent.hostname == hostname)
        return await self._session.scalar(stmt)

    async def get_by_agent_token_hash(self, token_hash: str) -> Agent | None:
        stmt = self._active_agents().where(
            Agent.agent_token_hash == token_hash,
            Agent.status.in_([AgentStatus.ACTIVE, AgentStatus.DISABLED]),
        )
        return await self._session.scalar(stmt)

    async def create_agent(
        self,
        *,
        hostname: str | None,
        os: AgentOS | None,
        status: AgentStatus,
    ) -> Agent:
        agent = Agent(hostname=hostname, os=os, status=status)
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

    async def add_to_group(self, agent_id: UUID, group_id: UUID) -> None:
        await self._session.execute(
            pg_insert(agent_group_memberships)
            .values(agent_id=agent_id, group_id=group_id)
            .on_conflict_do_nothing()
        )

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

    async def mark_stale_offline(self, cutoff: datetime) -> int:
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

    @staticmethod
    def _apply_filters(stmt, statuses, os, search):
        if statuses:
            stmt = stmt.where(Agent.status.in_(statuses))
        if os is not None:
            stmt = stmt.where(Agent.os == os)
        if search:
            stmt = stmt.where(Agent.hostname.ilike(f"%{search}%"))
        return stmt
