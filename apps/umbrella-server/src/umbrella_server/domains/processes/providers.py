"""Dishka-провайдер домена процессов."""

from dishka import Provider, Scope, provide

from umbrella_server.domains.processes.repository import ProcessRepository
from umbrella_server.domains.processes.service import ProcessService


class ProcessesProvider(Provider):
    scope = Scope.REQUEST

    process_repo = provide(ProcessRepository)
    process_service = provide(ProcessService)
