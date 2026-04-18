"""Async SQLAlchemy engine и session factory.

Engine — один на всё приложение (создаётся на старте в DI).
Session — одна на запрос/задачу (scope=REQUEST в DI).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from umbrella_server.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    """Создаёт AsyncEngine на основе настроек.
    """
    return create_async_engine(
        str(settings.database_url),
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Фабрика async-сессий, привязанная к engine.
    """
    return async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Контекст-менеджер для использования сессии вне FastAPI (CLI, скрипты, тесты).
    """
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()