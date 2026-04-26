"""Pydantic-схемы agents-домена."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from umbrella_server.domains.agents.models import AgentOS, AgentStatus


class AgentCreate(BaseModel):
    hostname: str = Field(min_length=1, max_length=255)
    os: AgentOS
    notes: str | None = None


class AgentUpdate(BaseModel):
    hostname: str | None = Field(default=None, min_length=1, max_length=255)
    status: AgentStatus | None = None
    notes: str | None = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hostname: str
    status: AgentStatus
    os: AgentOS
    os_version: str | None
    agent_version: str | None
    ip_address: str | None
    last_seen_at: datetime | None
    enrolled_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AgentCreateResponse(BaseModel):
    """Ответ на создание агента и регенерацию токена.

    enrollment_token отдаётся в СЫРОМ виде ОДИН РАЗ. Повторно его не получить —
    в БД хранится только hash. Если потерян — регенерировать через отдельную ручку.
    """
    model_config = ConfigDict(from_attributes=True)

    agent: AgentRead
    enrollment_token: str
    enrollment_token_expires_at: datetime


class AgentDecommissionTokenResponse(BaseModel):
    """Offline-токен для деинсталляции агента без обращения к серверу."""
    token: str
    expires_at: datetime


class AgentFilter(BaseModel):
    """Query-параметры list-endpoint'а. Используется через Depends()."""
    status: list[AgentStatus] | None = None
    os: AgentOS | None = None
    search: str | None = Field(default=None, max_length=255)


# ---------------------------------------------------------------------------
# Agent-facing schemas (enrollment, heartbeat, policy polling)
# ---------------------------------------------------------------------------

class AgentEnrollRequest(BaseModel):
    enrollment_token: str
    hostname: str = Field(min_length=1, max_length=255)
    os: AgentOS
    os_version: str | None = None
    agent_version: str | None = None
    ip_address: str | None = None
    csr_pem: str


class AgentEnrollResponse(BaseModel):
    agent_id: UUID
    agent_token: str
    cert_pem: str
    ca_cert_pem: str
    cert_expires_at: datetime
    policy_poll_interval_sec: int
    command_poll_interval_sec: int
    # PEM-публичный ключ для верификации offline-токенов деинсталляции.
    # None если сервер не настроен (SERVER_DECOMMISSION_KEY_PATH не задан).
    decommission_pubkey: str | None = None


class AgentHeartbeatRequest(BaseModel):
    os_version: str | None = None
    agent_version: str | None = None
    ip_address: str | None = None


class AgentRenewRequest(BaseModel):
    csr_pem: str


class AgentRenewResponse(BaseModel):
    cert_pem: str
    ca_cert_pem: str
    cert_expires_at: datetime