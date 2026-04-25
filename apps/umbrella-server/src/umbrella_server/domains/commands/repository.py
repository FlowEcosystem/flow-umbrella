"""Репозиторий домена команд."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.commands.models import Command, CommandStatus


class CommandRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, command_id: UUID) -> Command | None:
        return await self._session.scalar(
            select(Command).where(Command.id == command_id)
        )

    async def create(
        self,
        *,
        agent_id: UUID,
        type,
        payload: dict | None = None,
        issued_by_id: UUID | None = None,
        expires_at: datetime | None = None,
    ) -> Command:
        cmd = Command(
            agent_id=agent_id,
            type=type,
            status=CommandStatus.PENDING,
            payload=payload,
            issued_by_id=issued_by_id,
            expires_at=expires_at,
        )
        self._session.add(cmd)
        await self._session.flush()
        return cmd

    async def update(self, cmd: Command, fields: dict) -> Command:
        for key, value in fields.items():
            setattr(cmd, key, value)
        await self._session.flush()
        return cmd

    async def list_pending_for_agent(self, agent_id: UUID) -> list[Command]:
        """Возвращает команды в статусе PENDING для агента (очередь на выполнение)."""
        result = await self._session.scalars(
            select(Command)
            .where(
                Command.agent_id == agent_id,
                Command.status == CommandStatus.PENDING,
            )
            .order_by(Command.created_at.asc())
        )
        return list(result.all())

    async def list_for_agent(self, agent_id: UUID, *, limit: int = 50) -> list[Command]:
        result = await self._session.scalars(
            select(Command)
            .where(Command.agent_id == agent_id)
            .order_by(Command.created_at.desc())
            .limit(limit)
        )
        return list(result.all())
