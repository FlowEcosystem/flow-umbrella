"""Dishka-провайдер groups-домена."""

from dishka import Provider, Scope, provide

from umbrella_server.domains.groups.repository import GroupRepository
from umbrella_server.domains.groups.service import GroupService


class GroupsProvider(Provider):
    scope = Scope.REQUEST

    group_repo = provide(GroupRepository)
    group_service = provide(GroupService)