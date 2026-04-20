"""Dishka-провайдер instance-домена."""

from dishka import Provider, Scope, provide

from umbrella_server.domains.instance.repository import InstanceRepository
from umbrella_server.domains.instance.service import InstanceService


class InstanceProvider(Provider):
    scope = Scope.REQUEST

    instance_repo = provide(InstanceRepository)
    instance_service = provide(InstanceService)