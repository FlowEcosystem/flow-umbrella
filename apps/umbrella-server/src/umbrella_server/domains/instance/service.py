"""Сервис instance-домена."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.core.logging import get_logger
from umbrella_server.domains.instance.exceptions import InstanceNotInitializedError
from umbrella_server.domains.instance.models import BranchConfig
from umbrella_server.domains.instance.repository import InstanceRepository

logger = get_logger(__name__)


class InstanceService:
    def __init__(self, session: AsyncSession, repo: InstanceRepository) -> None:
        self._session = session
        self._repo = repo

    async def get(self) -> BranchConfig:
        config = await self._repo.get()
        if config is None:
            # Должно быть создано в bootstrap при старте — если попали сюда,
            # что-то пошло не так.
            raise InstanceNotInitializedError()
        return config

    async def update(self, fields: dict[str, Any]) -> BranchConfig:
        config = await self.get()
        # AnyHttpUrl приходит из Pydantic как URL-объект — приводим к str
        # для хранения.
        if "hq_base_url" in fields and fields["hq_base_url"] is not None:
            fields["hq_base_url"] = str(fields["hq_base_url"])
        await self._repo.update(config, fields)
        await self._session.commit()
        logger.info("instance_updated", fields=list(fields.keys()))
        return config