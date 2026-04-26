"""Сборка DI-контейнера из провайдеров."""

from dishka import AsyncContainer, make_async_container

from umbrella_server.di.providers.config import ConfigProvider
from umbrella_server.di.providers.db import DatabaseProvider

from umbrella_server.domains.auth.providers import AuthProvider
from umbrella_server.domains.instance.providers import InstanceProvider
from umbrella_server.domains.agents.providers import AgentsProvider
from umbrella_server.domains.groups.providers import GroupsProvider
from umbrella_server.domains.policies.providers import PoliciesProvider
from umbrella_server.domains.commands.providers import CommandsProvider
from umbrella_server.domains.metrics.providers import MetricsProvider


def build_container() -> AsyncContainer:
    """Собирает async-контейнер из всех провайдеров."""
    return make_async_container(
        ConfigProvider(),
        DatabaseProvider(),
        AuthProvider(),
        InstanceProvider(),
        AgentsProvider(),
        GroupsProvider(),
        PoliciesProvider(),
        CommandsProvider(),
        MetricsProvider(),
    )
