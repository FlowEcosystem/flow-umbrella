"""Dishka-провайдер policies-домена."""

from dishka import Provider, Scope, provide

from umbrella_server.domains.policies.repository import PolicyRepository, ServiceRepository
from umbrella_server.domains.policies.service import PolicyService, ServiceService


class PoliciesProvider(Provider):
    scope = Scope.REQUEST

    service_repo = provide(ServiceRepository)
    policy_repo = provide(PolicyRepository)
    service_service = provide(ServiceService)
    policy_service = provide(PolicyService)
