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
    AgentHostnameAlreadyExistsError,
    AgentNotFoundError,
    AgentTokenInvalidError,
    EnrollmentTokenExpiredError,
    EnrollmentTokenInvalidError,
)
from umbrella_server.domains.agents.models import Agent, AgentOS, AgentStatus, EnrollmentToken
from umbrella_server.domains.agents.repository import AgentRepository
from umbrella_server.pki import BranchCA
from umbrella_server.pki.decommission_key import DecommissionKey

logger = get_logger(__name__)

_TOKEN_BYTES = 32


def _make_token() -> tuple[str, str]:
    """Возвращает (raw, sha256_hex). raw показывается ОДИН РАЗ."""
    raw = secrets.token_urlsafe(_TOKEN_BYTES)
    return raw, hashlib.sha256(raw.encode()).hexdigest()


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

    # ── Enrollment tokens ────────────────────────────────────────────────────

    async def create_enrollment_token(
        self,
        *,
        note: str | None = None,
        expires_in_days: int | None = None,
        group_id: UUID | None = None,
        created_by_id: UUID | None = None,
    ) -> tuple[EnrollmentToken, str]:
        """Создаёт одноразовый enrollment-токен.

        Возвращает (token_record, raw_token). raw показывается ОДИН РАЗ.
        """
        raw, token_hash = _make_token()
        days = expires_in_days or self._settings.agent_enrollment_token_ttl_days
        expires_at = datetime.now(UTC) + timedelta(days=days)
        token = await self._repo.create_enrollment_token(
            token_hash=token_hash,
            expires_at=expires_at,
            note=note,
            group_id=group_id,
            created_by_id=created_by_id,
        )
        await self._session.commit()
        logger.info("enrollment_token_created", token_id=str(token.id), note=note)
        return token, raw

    async def list_enrollment_tokens(self) -> list[EnrollmentToken]:
        return await self._repo.list_enrollment_tokens()

    async def revoke_enrollment_token(self, token_id: UUID) -> None:
        token = await self._repo.get_enrollment_token_by_id(token_id)
        if token is None:
            raise AgentNotFoundError(token_id)
        await self._repo.delete_enrollment_token(token)
        await self._session.commit()
        logger.info("enrollment_token_revoked", token_id=str(token_id))

    # ── Agent queries ────────────────────────────────────────────────────────

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
        total = await self._repo.count_filtered(statuses=statuses, os=os, search=search)
        return items, total

    # ── Agent mutations ──────────────────────────────────────────────────────

    async def update(self, agent_id: UUID, fields: dict[str, Any]) -> Agent:
        agent = await self.get(agent_id)
        if "hostname" in fields and fields["hostname"] != agent.hostname:
            existing = await self._repo.get_by_hostname(fields["hostname"])
            if existing is not None:
                raise AgentHostnameAlreadyExistsError(fields["hostname"])
        await self._repo.update(agent, fields)
        await self._session.commit()
        logger.info("agent_updated", agent_id=str(agent.id), fields=list(fields.keys()))
        return agent

    async def delete(self, agent_id: UUID) -> None:
        """Soft-delete. Разрешён только для decommissioned агентов."""
        agent = await self.get(agent_id)
        if agent.status != AgentStatus.DECOMMISSIONED:
            raise ValueError(
                f"Agent {agent_id} is {agent.status.value}, not decommissioned. "
                "Send decommission command first."
            )
        await self._repo.soft_delete(agent)
        await self._session.commit()
        logger.info("agent_deleted", agent_id=str(agent.id))

    # ── Enrollment ───────────────────────────────────────────────────────────

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
        """Self-enrollment: находит токен, создаёт агента, сжигает токен.

        Возвращает (agent, raw_agent_token, cert_pem, ca_cert_pem).
        """
        if self._ca is None:
            raise ConfigurationError(
                "PKI not configured: set SERVER_PKI_CA_CERT_PATH and SERVER_PKI_CA_KEY_PATH"
            )

        token_hash = hashlib.sha256(enrollment_token.encode()).hexdigest()
        token_record = await self._repo.get_enrollment_token_by_hash(token_hash)

        if token_record is None or token_record.is_used:
            raise EnrollmentTokenInvalidError()

        now = datetime.now(UTC)
        if token_record.expires_at < now:
            raise EnrollmentTokenExpiredError()

        # Создаём агента динамически — hostname и OS берём из запроса.
        agent = await self._repo.create_agent(
            hostname=hostname,
            os=os,
            status=AgentStatus.ACTIVE,
        )

        cert_pem, serial, cert_expires_at = self._ca.sign_csr(csr_pem, agent.id)
        ca_cert_pem = self._ca.ca_cert_pem()

        raw_agent_token, agent_token_hash = _make_token()

        await self._repo.update(agent, {
            "os_version": os_version,
            "agent_version": agent_version,
            "ip_address": ip_address,
            "enrolled_at": now,
            "last_seen_at": now,
            "agent_token_hash": agent_token_hash,
            "cert_serial": str(serial),
            "cert_expires_at": cert_expires_at,
        })

        # Сжигаем токен.
        await self._repo.update_enrollment_token(token_record, {
            "used_at": now,
            "used_by_agent_id": agent.id,
        })

        # Авто-добавление в группу если задано.
        if token_record.group_id is not None:
            await self._repo.add_to_group(agent.id, token_record.group_id)

        await self._session.commit()
        logger.info("agent_enrolled", agent_id=str(agent.id), hostname=hostname)
        return agent, raw_agent_token, cert_pem, ca_cert_pem

    # ── Auth ─────────────────────────────────────────────────────────────────

    async def authenticate_by_cert(self, agent_id: UUID) -> Agent:
        """mTLS: принимает ACTIVE и DISABLED (disabled реактивируется при heartbeat)."""
        agent = await self._repo.get_by_id(agent_id)
        if agent is None or agent.status not in (AgentStatus.ACTIVE, AgentStatus.DISABLED):
            raise AgentTokenInvalidError()
        return agent

    async def authenticate(self, raw_agent_token: str) -> Agent:
        """Dev-fallback: Bearer token (только при agent_mtls=false)."""
        token_hash = hashlib.sha256(raw_agent_token.encode()).hexdigest()
        agent = await self._repo.get_by_agent_token_hash(token_hash)
        if agent is None:
            raise AgentTokenInvalidError()
        return agent

    # ── Heartbeat ────────────────────────────────────────────────────────────

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
        cutoff = datetime.now(UTC) - timedelta(seconds=self._settings.agent_offline_timeout_sec)
        count = await self._repo.mark_stale_offline(cutoff)
        if count:
            await self._session.commit()
        return count

    # ── Cert renewal ─────────────────────────────────────────────────────────

    async def renew_cert(self, agent: Agent, csr_pem: bytes) -> tuple[bytes, bytes]:
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

    # ── Offline decommission token ────────────────────────────────────────────

    def generate_decommission_token(self, agent: Agent) -> tuple[str, datetime]:
        if self._decommission_key is None:
            raise ConfigurationError(
                "Offline decommission tokens require SERVER_DECOMMISSION_KEY_PATH"
            )
        if agent.agent_token_hash is None:
            raise AgentNotFoundError(agent.id)
        return self._decommission_key.sign(str(agent.id))
