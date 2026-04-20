"""Dishka-провайдер agents-домена."""

from dishka import Provider, Scope, provide

from umbrella_server.domains.agents.repository import AgentRepository
from umbrella_server.domains.agents.service import AgentService


class AgentsProvider(Provider):
    scope = Scope.REQUEST

    agent_repo = provide(AgentRepository)
    agent_service = provide(AgentService)