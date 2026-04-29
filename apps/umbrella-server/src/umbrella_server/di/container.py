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
from umbrella_server.domains.processes.providers import ProcessesProvider
from umbrella_server.domains.audit.providers import AuditProvider
from umbrella_server.domains.releases.providers import ReleasesProvider


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
        ProcessesProvider(),
        AuditProvider(),
        ReleasesProvider(),
    )
