"""Сервис agents-домена."""

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import hashlib
import secrets

from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.core.config import Settings
from umbrella_server.core.logging import get_logger
from umbrella_server.core.exceptions import ConfigurationError
from umbrella_server.domains.agents.exceptions import (
    AgentAlreadyEnrolledError,
    AgentHostnameAlreadyExistsError,
    AgentNotFoundError,
    AgentTokenInvalidError,
    EnrollmentTokenExpiredError,
    EnrollmentTokenInvalidError,
)
from umbrella_server.domains.agents.models import Agent, AgentOS, AgentStatus
from umbrella_server.domains.agents.repository import AgentRepository
from umbrella_server.pki import BranchCA
from umbrella_server.pki.decommission_key import DecommissionKey

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
        ca: BranchCA | None,
        decommission_key: DecommissionKey | None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._repo = repo
        self._ca = ca
        self._decommission_key = decommission_key

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

    async def enroll(
        self,
        *,
        enrollment_token: str,
        csr_pem: bytes,
        hostname: str,
        os: AgentOS,
        os_version: str | None = None,
        agent_version: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[Agent, str, bytes, bytes]:
        """Enrollment агента по одноразовому токену.

        Возвращает (agent, raw_agent_token, cert_pem, ca_cert_pem).
        Токен enrollment сжигается — повторный вызов вернёт ошибку.
        """
        if self._ca is None:
            raise ConfigurationError(
                "PKI not configured: set SERVER_PKI_CA_CERT_PATH and SERVER_PKI_CA_KEY_PATH"
            )

        token_hash = hashlib.sha256(enrollment_token.encode("utf-8")).hexdigest()
        agent = await self._repo.get_by_enrollment_token_hash(token_hash)

        if agent is None or agent.enrolled_at is not None:
            raise EnrollmentTokenInvalidError()

        now = datetime.now(UTC)
        if agent.enrollment_token_expires_at and agent.enrollment_token_expires_at < now:
            raise EnrollmentTokenExpiredError()

        cert_pem, serial, cert_expires_at = self._ca.sign_csr(csr_pem, agent.id)
        ca_cert_pem = self._ca.ca_cert_pem()

        raw_agent_token = secrets.token_urlsafe(32)
        agent_token_hash = hashlib.sha256(raw_agent_token.encode("utf-8")).hexdigest()

        await self._repo.update(agent, {
            "hostname": hostname,
            "os": os,
            "os_version": os_version,
            "agent_version": agent_version,
            "ip_address": ip_address,
            "status": AgentStatus.ACTIVE,
            "enrolled_at": now,
            "last_seen_at": now,
            "enrollment_token_hash": None,
            "enrollment_token_expires_at": None,
            "agent_token_hash": agent_token_hash,
            "cert_serial": str(serial),
            "cert_expires_at": cert_expires_at,
        })
        await self._session.commit()
        logger.info("agent_enrolled", agent_id=str(agent.id), hostname=hostname)
        return agent, raw_agent_token, cert_pem, ca_cert_pem

    async def heartbeat(
        self,
        agent: Agent,
        *,
        os_version: str | None = None,
        agent_version: str | None = None,
        ip_address: str | None = None,
    ) -> Agent:
        fields: dict = {"last_seen_at": datetime.now(UTC)}
        if agent.status == AgentStatus.DISABLED:
            fields["status"] = AgentStatus.ACTIVE
            logger.info("agent_reactivated", agent_id=str(agent.id))
        if os_version is not None:
            fields["os_version"] = os_version
        if agent_version is not None:
            fields["agent_version"] = agent_version
        if ip_address is not None:
            fields["ip_address"] = ip_address
        await self._repo.update(agent, fields)
        await self._session.commit()
        return agent

    async def mark_stale_offline(self) -> int:
        """Переводит ACTIVE-агентов без свежего heartbeat в DISABLED.

        Порог берётся из настроек (agent_offline_timeout_sec).
        Возвращает количество переведённых агентов.
        """
        cutoff = datetime.now(UTC) - timedelta(seconds=self._settings.agent_offline_timeout_sec)
        count = await self._repo.mark_stale_offline(cutoff)
        if count:
            await self._session.commit()
        return count

    async def authenticate_by_cert(self, agent_id: UUID) -> Agent:
        """Для mTLS-режима: находит агента по ID из cert CN.

        Принимает ACTIVE и DISABLED — disabled-агент может прислать heartbeat
        и автоматически реактивироваться. PENDING/DECOMMISSIONED отклоняются.
        """
        agent = await self._repo.get_by_id(agent_id)
        if agent is None or agent.status not in (AgentStatus.ACTIVE, AgentStatus.DISABLED):
            raise AgentTokenInvalidError()
        return agent

    async def authenticate(self, raw_agent_token: str) -> Agent:
        """Dev-fallback: Bearer token auth (только при agent_mtls=false)."""
        token_hash = hashlib.sha256(raw_agent_token.encode("utf-8")).hexdigest()
        agent = await self._repo.get_by_agent_token_hash(token_hash)
        if agent is None:
            raise AgentTokenInvalidError()
        return agent

    async def renew_cert(self, agent: Agent, csr_pem: bytes) -> tuple[bytes, bytes]:
        """Перевыпуск сертификата агента по новому CSR без нового enrollment-токена.

        Агент должен быть ACTIVE. Возвращает (cert_pem, ca_cert_pem).
        """
        if self._ca is None:
            raise ConfigurationError(
                "PKI not configured: set SERVER_PKI_CA_CERT_PATH and SERVER_PKI_CA_KEY_PATH"
            )

        cert_pem, serial, cert_expires_at = self._ca.sign_csr(csr_pem, agent.id)
        ca_cert_pem = self._ca.ca_cert_pem()

        await self._repo.update(agent, {
            "cert_serial": str(serial),
            "cert_expires_at": cert_expires_at,
            "last_seen_at": datetime.now(UTC),
        })
        await self._session.commit()
        logger.info("agent_cert_renewed", agent_id=str(agent.id))
        return cert_pem, ca_cert_pem

    def generate_decommission_token(self, agent: Agent) -> tuple[str, datetime]:
        """Генерирует offline-токен деинсталляции (ECDSA P-256 подпись).

        Приватный ключ хранится только на сервере. Агент верифицирует подпись
        публичным ключом, полученным при enrollment, — без обращения к серверу.
        """
        if self._decommission_key is None:
            raise ConfigurationError(
                "Offline decommission tokens require SERVER_DECOMMISSION_KEY_PATH"
            )
        if agent.agent_token_hash is None:
            raise AgentNotFoundError(agent.id)
        return self._decommission_key.sign(str(agent.id))

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