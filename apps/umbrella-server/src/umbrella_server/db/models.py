"""Агрегатор всех моделей для Alembic autogenerate."""

from umbrella_server.db.base import Base
from umbrella_server.domains.auth.models import Admin, RefreshToken 
from umbrella_server.domains.instance.models import BranchConfig
from umbrella_server.domains.agents.models import Agent, AgentOS, AgentStatus
from umbrella_server.domains.groups.models import Group, agent_group_memberships
from umbrella_server.domains.policies.models import (
    Policy, PolicyAction, PolicyKind, PolicySource, PolicyRuleType,
    Service, policy_services, policy_group_assignments, policy_agent_assignments,
)
from umbrella_server.domains.commands.models import Command, CommandType, CommandStatus
from umbrella_server.domains.metrics.models import AgentMetric

__all__ = [
    "Base", "Admin", "RefreshToken", "BranchConfig",
    "Agent", "AgentOS", "AgentStatus",
    "Group", "agent_group_memberships",
    "Policy", "PolicyAction", "PolicyKind", "PolicySource", "PolicyRuleType",
    "Service", "policy_services", "policy_group_assignments", "policy_agent_assignments",
    "Command", "CommandType", "CommandStatus",
    "AgentMetric",
]