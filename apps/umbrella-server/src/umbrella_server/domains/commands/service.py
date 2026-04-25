"""Сервис домена команд."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.core.logging import get_logger
from umbrella_server.domains.commands.exceptions import (
    CommandInvalidStatusError,
    CommandNotFoundError,
)
from umbrella_server.domains.commands.models import Command, CommandStatus, CommandType
from umbrella_server.domains.commands.repository import CommandRepository

logger = get_logger(__name__)

# Если expires_in_sec не задан — командa живёт 1 час.
_DEFAULT_COMMAND_TTL_SEC = 3600


class CommandService:
    def __init__(self, session: AsyncSession, repo: CommandRepository) -> None:
        self._session = session
        self._repo = repo

    async def issue(
        self,
        *,
        agent_id: UUID,
        type: CommandType,
        payload: dict | None = None,
        issued_by_id: UUID | None = None,
        expires_in_sec: int | None = None,
    ) -> Command:
        ttl = expires_in_sec if expires_in_sec is not None else _DEFAULT_COMMAND_TTL_SEC
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl)
        cmd = await self._repo.create(
            agent_id=agent_id,
            type=type,
            payload=payload,
            issued_by_id=issued_by_id,
            expires_at=expires_at,
        )
        await self._session.commit()
        logger.info("command_issued", command_id=str(cmd.id), agent_id=str(agent_id), type=type.value)
        return cmd

    async def get(self, command_id: UUID) -> Command:
        cmd = await self._repo.get_by_id(command_id)
        if cmd is None:
            raise CommandNotFoundError(command_id)
        return cmd

    async def list_for_agent(self, agent_id: UUID) -> list[Command]:
        return await self._repo.list_for_agent(agent_id)

    async def poll_pending(self, agent_id: UUID) -> list[Command]:
        """Возвращает PENDING команды и помечает их как SENT."""
        cmds = await self._repo.list_pending_for_agent(agent_id)
        now = datetime.now(UTC)
        for cmd in cmds:
            await self._repo.update(cmd, {"status": CommandStatus.SENT, "sent_at": now})
        if cmds:
            await self._session.commit()
        return cmds

    async def submit_result(
        self,
        command_id: UUID,
        agent_id: UUID,
        *,
        status: CommandStatus,
        result: dict | None = None,
        error_message: str | None = None,
    ) -> Command:
        cmd = await self.get(command_id)
        if cmd.agent_id != agent_id:
            raise CommandNotFoundError(command_id)
        if cmd.status not in (CommandStatus.SENT, CommandStatus.ACKNOWLEDGED):
            raise CommandInvalidStatusError(command_id, cmd.status.value, "sent/acknowledged")

        now = datetime.now(UTC)
        await self._repo.update(cmd, {
            "status": status,
            "result": result,
            "error_message": error_message,
            "completed_at": now,
        })
        await self._session.commit()
        logger.info(
            "command_result_received",
            command_id=str(command_id),
            status=status.value,
        )
        return cmd
