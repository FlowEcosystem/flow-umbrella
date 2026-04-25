"""Репозиторий groups-домена."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.agents.models import Agent
from umbrella_server.domains.groups.models import Group, agent_group_memberships


class GroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _active_groups(self) -> Select[tuple[Group]]:
        return select(Group).where(Group.deleted_at.is_(None))

    async def get_by_id(self, group_id: UUID) -> Group | None:
        stmt = self._active_groups().where(Group.id == group_id)
        return await self._session.scalar(stmt)

    async def get_by_name(self, name: str) -> Group | None:
        stmt = self._active_groups().where(Group.name == name)
        return await self._session.scalar(stmt)

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
        color: str | None = None,
    ) -> Group:
        group = Group(name=name, description=description, color=color)
        self._session.add(group)
        await self._session.flush()
        return group

    async def update(self, group: Group, fields: dict) -> Group:
        for key, value in fields.items():
            setattr(group, key, value)
        await self._session.flush()
        return group

    async def soft_delete(self, group: Group) -> None:
        group.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def list(self, *, limit: int, offset: int) -> list[Group]:
        stmt = (
            self._active_groups()
            .order_by(Group.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def count(self) -> int:
        stmt = (
            select(func.count())
            .select_from(Group)
            .where(Group.deleted_at.is_(None))
        )
        return await self._session.scalar(stmt) or 0

    async def count_agents(self, group_id: UUID) -> int:
        """Количество агентов в группе (только активные агенты)."""
        stmt = (
            select(func.count())
            .select_from(agent_group_memberships)
            .join(Agent, Agent.id == agent_group_memberships.c.agent_id)
            .where(
                agent_group_memberships.c.group_id == group_id,
                Agent.deleted_at.is_(None),
            )
        )
        return await self._session.scalar(stmt) or 0

    async def counts_agents_bulk(self, group_ids: list[UUID]) -> dict[UUID, int]:
        """Batch-версия count_agents: один SQL на много групп.

        Используется в list-endpoint'е, чтобы не делать N+1.
        """
        if not group_ids:
            return {}
        stmt = (
            select(
                agent_group_memberships.c.group_id,
                func.count(agent_group_memberships.c.agent_id),
            )
            .join(Agent, Agent.id == agent_group_memberships.c.agent_id)
            .where(
                agent_group_memberships.c.group_id.in_(group_ids),
                Agent.deleted_at.is_(None),
            )
            .group_by(agent_group_memberships.c.group_id)
        )
        result = await self._session.execute(stmt)
        counts = {row[0]: row[1] for row in result.all()}
        # Для групп без агентов — вернуть 0, не отсутствие ключа.
        return {gid: counts.get(gid, 0) for gid in group_ids}

    async def list_agents(
        self,
        group_id: UUID,
        *,
        limit: int,
        offset: int,
    ) -> list[Agent]:
        stmt = (
            select(Agent)
            .join(agent_group_memberships, agent_group_memberships.c.agent_id == Agent.id)
            .where(
                agent_group_memberships.c.group_id == group_id,
                Agent.deleted_at.is_(None),
            )
            .order_by(Agent.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def add_agents(
        self,
        group_id: UUID,
        agent_ids: list[UUID],
    ) -> tuple[int, int]:
        """Добавляет агентов в группу. Возвращает (added, already_in_group).

        Дубликаты игнорирует — нет смысла падать, если агент уже там.
        """
        existing_stmt = select(agent_group_memberships.c.agent_id).where(
            agent_group_memberships.c.group_id == group_id,
            agent_group_memberships.c.agent_id.in_(agent_ids),
        )
        existing = await self._session.scalars(existing_stmt)
        existing_ids = set(existing.all())

        to_add = [aid for aid in agent_ids if aid not in existing_ids]
        if to_add:
            await self._session.execute(
                insert(agent_group_memberships),
                [{"agent_id": aid, "group_id": group_id} for aid in to_add],
            )
            await self._session.flush()

        return len(to_add), len(existing_ids)

    async def remove_agent(self, group_id: UUID, agent_id: UUID) -> bool:
        """Убирает агента из группы. Возвращает True если было что удалять."""
        stmt = delete(agent_group_memberships).where(
            agent_group_memberships.c.group_id == group_id,
            agent_group_memberships.c.agent_id == agent_id,
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0 # pyright: ignore[reportAttributeAccessIssue]

    async def remove_all_memberships(self, group_id: UUID) -> int:
        """Удаляет все memberships группы. Для soft-delete группы."""
        stmt = delete(agent_group_memberships).where(
            agent_group_memberships.c.group_id == group_id
        )
        result = await self._session.execute(stmt)
        return result.rowcount # pyright: ignore[reportAttributeAccessIssue]

    async def list_groups_for_agent(self, agent_id: UUID) -> list[Group]:
        """Группы, в которых состоит агент."""
        stmt = (
            self._active_groups()
            .join(agent_group_memberships, agent_group_memberships.c.group_id == Group.id)
            .where(agent_group_memberships.c.agent_id == agent_id)
            .order_by(Group.name)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def verify_agents_exist(self, agent_ids: list[UUID]) -> list[UUID]:
        """Возвращает ID тех агентов, которых нет в БД (или soft-deleted)."""
        stmt = select(Agent.id).where(
            Agent.id.in_(agent_ids),
            Agent.deleted_at.is_(None),
        )
        found = await self._session.scalars(stmt)
        found_set = set(found.all())
        return [aid for aid in agent_ids if aid not in found_set]