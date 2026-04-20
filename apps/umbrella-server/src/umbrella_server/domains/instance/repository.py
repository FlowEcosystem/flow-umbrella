"""Репозиторий instance-домена."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.instance.models import BranchConfig


class InstanceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self) -> BranchConfig | None:
        stmt = select(BranchConfig).where(BranchConfig.id == 1)
        return await self._session.scalar(stmt)

    async def create_default(self, branch_name: str) -> BranchConfig:
        config = BranchConfig(id=1, branch_name=branch_name)
        self._session.add(config)
        await self._session.flush()
        return config

    async def update(self, config: BranchConfig, fields: dict) -> BranchConfig:
        for key, value in fields.items():
            setattr(config, key, value)
        await self._session.flush()
        return config