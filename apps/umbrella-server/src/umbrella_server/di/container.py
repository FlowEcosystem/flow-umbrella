"""Сборка DI-контейнера из провайдеров."""

from dishka import AsyncContainer, make_async_container

from umbrella_server.di.providers.config import ConfigProvider
from umbrella_server.di.providers.db import DatabaseProvider


def build_container() -> AsyncContainer:
    """Собирает async-контейнер из всех провайдеров.
    """
    return make_async_container(
        ConfigProvider(),
        DatabaseProvider(),
    )