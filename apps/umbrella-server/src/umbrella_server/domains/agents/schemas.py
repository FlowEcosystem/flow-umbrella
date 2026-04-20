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


class AgentFilter(BaseModel):
    """Query-параметры list-endpoint'а. Используется через Depends()."""
    status: list[AgentStatus] | None = None
    os: AgentOS | None = None
    search: str | None = Field(default=None, max_length=255)