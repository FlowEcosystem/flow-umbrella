"""Dishka-провайдер agents-домена."""

from dishka import Provider, Scope, provide

from umbrella_server.core.config import Settings
from umbrella_server.domains.agents.repository import AgentRepository
from umbrella_server.domains.agents.service import AgentService
from umbrella_server.pki import BranchCA


class AgentsProvider(Provider):
    scope = Scope.REQUEST

    agent_repo = provide(AgentRepository)
    agent_service = provide(AgentService)

    @provide(scope=Scope.APP)
    def branch_ca(self, settings: Settings) -> BranchCA | None:
        if not settings.pki_ca_cert_path or not settings.pki_ca_key_path:
            return None
        return BranchCA.ensure(
            cert_path=settings.pki_ca_cert_path,
            key_path=settings.pki_ca_key_path,
            branch_name="Umbrella",
        )
