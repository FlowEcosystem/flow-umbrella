"""Сервис agents-домена."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import secrets
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.core.config import Settings
from umbrella_server.core.logging import get_logger
from umbrella_server.domains.agents.exceptions import (
    AgentAlreadyEnrolledError,
    AgentHostnameAlreadyExistsError,
    AgentNotFoundError,
)
from umbrella_server.domains.agents.models import Agent, AgentOS, AgentStatus
from umbrella_server.domains.agents.repository import AgentRepository

logger = get_logger(__name__)


# Такой же формат, как refresh-токены у админов: 32 случайных байта,
# urlsafe-base64 → ~43 символа. Достаточно для SHA-256 по hash'у.
_ENROLLMENT_TOKEN_BYTES = 32


def _generate_enrollment_token() -> tuple[str, str]:
    """Возвращает (raw, hash). raw отдаётся админу ОДИН РАЗ."""
    raw = secrets.token_urlsafe(_ENROLLMENT_TOKEN_BYTES)
    token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return raw, token_hash


class AgentService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        repo: AgentRepository,
    ) -> None:
        self._session = session
        self._settings = settings
        self._repo = repo

    async def get(self, agent_id: UUID) -> Agent:
        agent = await self._repo.get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)
        return agent

    async def list(
        self,
        *,
        limit: int,
        offset: int,
        statuses: list[AgentStatus] | None = None,
        os: AgentOS | None = None,
        search: str | None = None,
    ) -> tuple[list[Agent], int]:
        items = await self._repo.list_filtered(
            limit=limit, offset=offset, statuses=statuses, os=os, search=search,
        )
        total = await self._repo.count_filtered(
            statuses=statuses, os=os, search=search,
        )
        return items, total

    async def create(
        self,
        *,
        hostname: str,
        os: AgentOS,
        notes: str | None = None,
    ) -> tuple[Agent, str]:
        """Создаёт агента в статусе pending и enrollment-токен.

        Возвращает (agent, raw_enrollment_token). raw показывается админу
        один раз — в БД только hash.
        """
        existing = await self._repo.get_by_hostname(hostname)
        if existing is not None:
            raise AgentHostnameAlreadyExistsError(hostname)

        raw_token, token_hash = _generate_enrollment_token()
        expires_at = datetime.now(UTC) + timedelta(
            days=self._settings.agent_enrollment_token_ttl_days
        )

        agent = await self._repo.create(
            hostname=hostname,
            os=os,
            status=AgentStatus.PENDING,
            enrollment_token_hash=token_hash,
            enrollment_token_expires_at=expires_at,
            notes=notes,
        )
        await self._session.commit()
        logger.info(
            "agent_created",
            agent_id=agent.id,
            hostname=hostname,
            os=os.value,
        )
        return agent, raw_token

    async def update(self, agent_id: UUID, fields: dict[str, Any]) -> Agent:
        agent = await self.get(agent_id)

        # Смена hostname — проверить уникальность.
        if "hostname" in fields and fields["hostname"] != agent.hostname:
            existing = await self._repo.get_by_hostname(fields["hostname"])
            if existing is not None:
                raise AgentHostnameAlreadyExistsError(fields["hostname"])

        await self._repo.update(agent, fields)
        await self._session.commit()
        logger.info("agent_updated", agent_id=agent.id, fields=list(fields.keys()))
        return agent

    async def delete(self, agent_id: UUID) -> None:
        agent = await self.get(agent_id)
        await self._repo.soft_delete(agent)
        await self._session.commit()
        logger.info("agent_deleted", agent_id=agent.id)

    async def regenerate_enrollment_token(self, agent_id: UUID) -> tuple[Agent, str]:
        """Генерит новый enrollment-токен для агента.

        Используется, если админ потерял предыдущий токен до установки агента.
        Нельзя делать для уже enrolled агента — тогда его сертификат надо
        отзывать отдельной процедурой.
        """
        agent = await self.get(agent_id)
        if agent.enrolled_at is not None:
            raise AgentAlreadyEnrolledError(agent.id)

        raw_token, token_hash = _generate_enrollment_token()
        expires_at = datetime.now(UTC) + timedelta(
            days=self._settings.agent_enrollment_token_ttl_days
        )

        await self._repo.update(
            agent,
            {
                "enrollment_token_hash": token_hash,
                "enrollment_token_expires_at": expires_at,
            },
        )
        await self._session.commit()
        logger.info("agent_enrollment_token_regenerated", agent_id=agent.id)
        return agent, raw_token