"""Провайдеры БД: engine, session factory, session."""

from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from umbrella_server.core.config import Settings
from umbrella_server.db.session import create_engine, create_session_factory


class DatabaseProvider(Provider):
    """Провайдеры для работы с БД.
    """

    @provide(scope=Scope.APP)
    async def engine(self, settings: Settings) -> AsyncIterator[AsyncEngine]:
        """Async engine. Создаётся на старте, disposed на shutdown.
        """
        engine = create_engine(settings)
        yield engine
        await engine.dispose()

    @provide(scope=Scope.APP)
    def session_factory(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        """Фабрика сессий. Лёгкая, один инстанс на приложение."""
        return create_session_factory(engine)

    @provide(scope=Scope.REQUEST)
    async def session(
        self,
        factory: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        """Сессия на HTTP-запрос.
        """
        async with factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise