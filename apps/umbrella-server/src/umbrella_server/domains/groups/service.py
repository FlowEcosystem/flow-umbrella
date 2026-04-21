"""Сервис groups-домена."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.core.logging import get_logger
from umbrella_server.domains.agents.models import Agent
from umbrella_server.domains.groups.exceptions import (
    AgentsNotFoundError,
    GroupNameAlreadyExistsError,
    GroupNotFoundError,
)
from umbrella_server.domains.groups.models import Group
from umbrella_server.domains.groups.repository import GroupRepository

logger = get_logger(__name__)


class GroupService:
    def __init__(self, session: AsyncSession, repo: GroupRepository) -> None:
        self._session = session
        self._repo = repo

    async def get(self, group_id: UUID) -> Group:
        group = await self._repo.get_by_id(group_id)
        if group is None:
            raise GroupNotFoundError(group_id)
        return group

    async def list(
        self, *, limit: int, offset: int
    ) -> tuple[list[Group], dict[UUID, int], int]:
        """Возвращает (groups, agent_counts, total).

        agent_counts — dict {group_id: N}, собранный одним bulk-запросом,
        чтобы не было N+1 в роутере.
        """
        items = await self._repo.list(limit=limit, offset=offset)
        total = await self._repo.count()
        counts = await self._repo.counts_agents_bulk([g.id for g in items])
        return items, counts, total

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        color: str | None = None,
    ) -> Group:
        existing = await self._repo.get_by_name(name)
        if existing is not None:
            raise GroupNameAlreadyExistsError(name)
        group = await self._repo.create(
            name=name, description=description, color=color
        )
        await self._session.commit()
        logger.info("group_created", group_id=group.id, name=name)
        return group

    async def update(self, group_id: UUID, fields: dict[str, Any]) -> Group:
        group = await self.get(group_id)
        if "name" in fields and fields["name"] != group.name:
            existing = await self._repo.get_by_name(fields["name"])
            if existing is not None:
                raise GroupNameAlreadyExistsError(fields["name"])
        await self._repo.update(group, fields)
        await self._session.commit()
        logger.info("group_updated", group_id=group.id, fields=list(fields.keys()))
        return group

    async def delete(self, group_id: UUID) -> None:
        group = await self.get(group_id)
        # Хард-удаление memberships ДО soft-delete группы —
        removed = await self._repo.remove_all_memberships(group.id)
        await self._repo.soft_delete(group)
        await self._session.commit()
        logger.info(
            "group_deleted", group_id=group.id, memberships_removed=removed
        )

    async def list_agents(
        self, group_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[Agent], int]:
        # Проверяем, что группа существует — иначе вернём пустой список,
        # но клиент не поймёт, почему.
        await self.get(group_id)
        items = await self._repo.list_agents(group_id, limit=limit, offset=offset)
        total = await self._repo.count_agents(group_id)
        return items, total
    
    async def count_agents(self, group_id: UUID) -> int:
        return await self._repo.count_agents(group_id)

    async def add_agents(
        self, group_id: UUID, agent_ids: list[UUID]
    ) -> tuple[int, int]:
        await self.get(group_id)

        # Дедупликация внутри запроса — клиент может прислать дубликаты.
        unique_ids = list(dict.fromkeys(agent_ids))

        missing = await self._repo.verify_agents_exist(unique_ids)
        if missing:
            raise AgentsNotFoundError(missing)

        added, already = await self._repo.add_agents(group_id, unique_ids)
        await self._session.commit()
        logger.info(
            "group_agents_added",
            group_id=group_id,
            added=added,
            already_in_group=already,
        )
        return added, already

    async def remove_agent(self, group_id: UUID, agent_id: UUID) -> None:
        await self.get(group_id)
        # Не кидаем, если membership'а не было — идемпотентная операция.
        # DELETE несуществующего = всё равно "после вызова не существует".
        removed = await self._repo.remove_agent(group_id, agent_id)
        await self._session.commit()
        logger.info(
            "group_agent_removed",
            group_id=group_id,
            agent_id=agent_id,
            existed=removed,
        )