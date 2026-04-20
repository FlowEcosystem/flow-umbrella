"""Инициализация instance при первом запуске.

Вызывается из main.lifespan() до того, как сервер начнёт принимать запросы.
"""

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from umbrella_server.core.logging import get_logger
from umbrella_server.domains.instance.repository import InstanceRepository

logger = get_logger(__name__)

_DEFAULT_BRANCH_NAME = "Unnamed branch"


async def ensure_instance(factory: async_sessionmaker[AsyncSession]) -> None:
    """Создаёт branch_config с дефолтами, если его ещё нет.

    Идемпотентно — можно вызывать при каждом старте.
    """
    async with factory() as session:
        repo = InstanceRepository(session)
        config = await repo.get()
        if config is not None:
            logger.info(
                "instance_loaded",
                branch_id=str(config.branch_id),
                branch_name=config.branch_name,
                hq_sync_enabled=config.hq_sync_enabled,
            )
            return

        config = await repo.create_default(_DEFAULT_BRANCH_NAME)
        await session.commit()
        logger.info(
            "instance_initialized",
            branch_id=str(config.branch_id),
            branch_name=config.branch_name,
        )