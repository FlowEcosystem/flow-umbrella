"""Агрегатор всех моделей для Alembic autogenerate."""

from umbrella_server.db.base import Base
from umbrella_server.domains.auth.models import Admin, RefreshToken 
from umbrella_server.domains.instance.models import BranchConfig
from umbrella_server.domains.agents.models import Agent, AgentOS, AgentStatus
from umbrella_server.domains.groups.models import Group, agent_group_memberships

__all__ = ["Base", "Admin", "RefreshToken", "BranchConfig", "Agent", "AgentOS", "AgentStatus", "Group", "agent_group_memberships"]