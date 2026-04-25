"""Pydantic-схемы policies-домена."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from umbrella_server.domains.policies.models import PolicyAction, PolicyKind, PolicyRuleType, PolicySource


class PolicyRuleItem(BaseModel):
    type: PolicyRuleType
    value: str = Field(min_length=1, max_length=2048)


# --- Service ---

class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=255)
    description: str | None = None
    kind: PolicyKind = PolicyKind.TRAFFIC
    rules: list[PolicyRuleItem] = Field(default_factory=list, max_length=500)
    is_active: bool = True


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    rules: list[PolicyRuleItem] | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    category: str
    description: str | None
    kind: PolicyKind
    source: PolicySource
    is_active: bool
    rules: list[dict]
    rules_count: int
    created_at: datetime
    updated_at: datetime


# --- Policy ---

class PolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    kind: PolicyKind = PolicyKind.TRAFFIC
    action: PolicyAction
    is_active: bool = True
    service_ids: list[UUID] = Field(default_factory=list)
    custom_rules: list[PolicyRuleItem] = Field(default_factory=list, max_length=500)


class PolicyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    action: PolicyAction | None = None
    is_active: bool | None = None
    service_ids: list[UUID] | None = None
    custom_rules: list[PolicyRuleItem] | None = Field(default=None, max_length=500)


class PolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    kind: PolicyKind
    source: PolicySource
    action: PolicyAction
    is_active: bool
    is_global: bool
    overridable: bool
    version: int
    hq_policy_id: UUID | None
    services: list[ServiceRead]
    custom_rules: list[dict]
    rules_count: int
    created_at: datetime
    updated_at: datetime


# --- Policy assignments ---

class PolicyAssignRequest(BaseModel):
    is_global: bool = False
    group_ids: list[UUID] = Field(default_factory=list)
    agent_ids: list[UUID] = Field(default_factory=list)


class PolicyGroupItem(BaseModel):
    group_id: UUID
    name: str
    color: str | None


class PolicyAgentItem(BaseModel):
    agent_id: UUID
    hostname: str


class PolicyAssignmentsRead(BaseModel):
    is_global: bool
    groups: list[PolicyGroupItem]
    agents: list[PolicyAgentItem]


# --- Agent-facing ---

class AgentPolicyItem(BaseModel):
    id: UUID
    name: str
    kind: PolicyKind
    action: PolicyAction
    version: int
    rules: list[dict]


# --- Admin: effective policies for an agent ---

class EffectivePolicyItem(BaseModel):
    id: UUID
    name: str
    kind: PolicyKind
    action: PolicyAction
    is_active: bool
    is_global: bool
    version: int
    rules_count: int
