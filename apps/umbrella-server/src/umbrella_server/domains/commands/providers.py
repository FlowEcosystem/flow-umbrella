"""Dishka-провайдер домена команд."""

from dishka import Provider, Scope, provide

from umbrella_server.domains.commands.repository import CommandRepository
from umbrella_server.domains.commands.service import CommandService


class CommandsProvider(Provider):
    scope = Scope.REQUEST

    command_repo = provide(CommandRepository)
    command_service = provide(CommandService)
