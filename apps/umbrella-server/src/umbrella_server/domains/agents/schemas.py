"""Pydantic-схемы agents-домена."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from umbrella_server.domains.agents.models import AgentOS, AgentStatus


# ── Enrollment tokens ────────────────────────────────────────────────────────

class EnrollmentTokenCreate(BaseModel):
    note: str | None = Field(default=None, max_length=255)
    expires_in_days: int | None = Field(default=None, ge=1, le=365)
    group_id: UUID | None = None


class EnrollmentTokenRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    note: str | None
    expires_at: datetime
    group_id: UUID | None
    used_at: datetime | None
    used_by_agent_id: UUID | None
    created_at: datetime


class EnrollmentTokenCreated(BaseModel):
    """Ответ при создании токена. raw_token показывается ОДИН РАЗ."""
    token: EnrollmentTokenRead
    raw_token: str


# ── Agents ───────────────────────────────────────────────────────────────────

class AgentUpdate(BaseModel):
    """Только поля, которые может менять администратор вручную."""
    notes: str | None = None


class AgentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    hostname: str | None
    status: AgentStatus
    os: AgentOS | None
    os_version: str | None
    agent_version: str | None
    ip_address: str | None
    last_seen_at: datetime | None
    enrolled_at: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AgentDecommissionTokenResponse(BaseModel):
    token: str
    expires_at: datetime


class AgentFilter(BaseModel):
    status: list[AgentStatus] | None = None
    os: AgentOS | None = None
    search: str | None = Field(default=None, max_length=255)


# ── Agent-facing schemas ─────────────────────────────────────────────────────

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
    metrics_push_interval_sec: int
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
