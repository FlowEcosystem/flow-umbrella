"""Репозиторий policies-домена."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Select, delete, func, insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.policies.models import (
    Policy, PolicyAction, PolicyKind, PolicySource, Service,
    policy_agent_assignments, policy_group_assignments, policy_services,
)


class ServiceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _active(self) -> Select[tuple[Service]]:
        return select(Service).where(Service.deleted_at.is_(None))

    async def get_by_id(self, service_id: UUID) -> Service | None:
        return await self._session.scalar(self._active().where(Service.id == service_id))

    async def get_by_ids(self, service_ids: list[UUID]) -> list[Service]:
        if not service_ids:
            return []
        result = await self._session.scalars(self._active().where(Service.id.in_(service_ids)))
        return list(result.all())

    async def get_by_name(self, name: str) -> Service | None:
        return await self._session.scalar(self._active().where(Service.name == name))

    async def list(
        self, *, limit: int, offset: int,
        source: PolicySource | None = None,
        category: str | None = None,
        kind: PolicyKind | None = None,
    ) -> list[Service]:
        stmt = self._active().order_by(Service.category, Service.name).limit(limit).offset(offset)
        if source is not None:
            stmt = stmt.where(Service.source == source)
        if category is not None:
            stmt = stmt.where(Service.category == category)
        if kind is not None:
            stmt = stmt.where(Service.kind == kind)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def count(
        self, *, source: PolicySource | None = None,
        category: str | None = None,
        kind: PolicyKind | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Service).where(Service.deleted_at.is_(None))
        if source is not None:
            stmt = stmt.where(Service.source == source)
        if category is not None:
            stmt = stmt.where(Service.category == category)
        if kind is not None:
            stmt = stmt.where(Service.kind == kind)
        return await self._session.scalar(stmt) or 0

    async def create(
        self, *, name: str, category: str, description: str | None,
        rules: list[dict], is_active: bool = True,
        kind: PolicyKind = PolicyKind.TRAFFIC,
        source: PolicySource = PolicySource.LOCAL,
    ) -> Service:
        service = Service(
            name=name, category=category, description=description,
            rules=rules, is_active=is_active, kind=kind, source=source,
        )
        self._session.add(service)
        await self._session.flush()
        return service

    async def update(self, service: Service, fields: dict[str, Any]) -> Service:
        for key, value in fields.items():
            setattr(service, key, value)
        await self._session.flush()
        return service

    async def soft_delete(self, service: Service) -> None:
        service.deleted_at = datetime.now(UTC)
        await self._session.flush()


class PolicyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _active(self) -> Select[tuple[Policy]]:
        return select(Policy).where(Policy.deleted_at.is_(None))

    async def get_by_id(self, policy_id: UUID) -> Policy | None:
        return await self._session.scalar(self._active().where(Policy.id == policy_id))

    async def get_by_name(self, name: str) -> Policy | None:
        return await self._session.scalar(self._active().where(Policy.name == name))

    async def list(
        self, *, limit: int, offset: int,
        source: PolicySource | None = None,
        action: PolicyAction | None = None,
        is_active: bool | None = None,
        kind: PolicyKind | None = None,
    ) -> list[Policy]:
        stmt = self._active().order_by(Policy.created_at.desc()).limit(limit).offset(offset)
        if source is not None:
            stmt = stmt.where(Policy.source == source)
        if action is not None:
            stmt = stmt.where(Policy.action == action)
        if is_active is not None:
            stmt = stmt.where(Policy.is_active == is_active)
        if kind is not None:
            stmt = stmt.where(Policy.kind == kind)
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def count(
        self, *, source: PolicySource | None = None,
        action: PolicyAction | None = None,
        is_active: bool | None = None,
        kind: PolicyKind | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Policy).where(Policy.deleted_at.is_(None))
        if source is not None:
            stmt = stmt.where(Policy.source == source)
        if action is not None:
            stmt = stmt.where(Policy.action == action)
        if is_active is not None:
            stmt = stmt.where(Policy.is_active == is_active)
        if kind is not None:
            stmt = stmt.where(Policy.kind == kind)
        return await self._session.scalar(stmt) or 0

    async def create(
        self, *, name: str, description: str | None, action: PolicyAction,
        is_active: bool, custom_rules: list[dict], services: list[Service],
        kind: PolicyKind = PolicyKind.TRAFFIC,
        source: PolicySource = PolicySource.LOCAL,
        overridable: bool = False, version: int = 0, hq_policy_id: UUID | None = None,
    ) -> Policy:
        policy = Policy(
            name=name, description=description, action=action,
            is_active=is_active, custom_rules=custom_rules,
            kind=kind, source=source, overridable=overridable,
            version=version, hq_policy_id=hq_policy_id,
        )
        self._session.add(policy)
        await self._session.flush()
        if services:
            await self._session.execute(
                insert(policy_services),
                [{"policy_id": policy.id, "service_id": s.id} for s in services],
            )
            await self._session.flush()
        await self._session.refresh(policy, ["services"])
        return policy

    async def update(
        self, policy: Policy, fields: dict[str, Any],
        services: list[Service] | None = None,
    ) -> Policy:
        for key, value in fields.items():
            setattr(policy, key, value)
        if services is not None:
            await self._session.execute(
                delete(policy_services).where(policy_services.c.policy_id == policy.id)
            )
            if services:
                await self._session.execute(
                    insert(policy_services),
                    [{"policy_id": policy.id, "service_id": s.id} for s in services],
                )
            await self._session.flush()
            await self._session.refresh(policy, ["services"])
        else:
            await self._session.flush()
        return policy

    async def soft_delete(self, policy: Policy) -> None:
        policy.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def get_assignments(
        self, policy_id: UUID,
    ) -> tuple[bool, list[UUID], list[UUID]]:
        policy = await self.get_by_id(policy_id)
        is_global = policy.is_global if policy else False

        group_rows = await self._session.execute(
            select(policy_group_assignments.c.group_id)
            .where(policy_group_assignments.c.policy_id == policy_id)
        )
        group_ids = [r[0] for r in group_rows.all()]

        agent_rows = await self._session.execute(
            select(policy_agent_assignments.c.agent_id)
            .where(policy_agent_assignments.c.policy_id == policy_id)
        )
        agent_ids = [r[0] for r in agent_rows.all()]

        return is_global, group_ids, agent_ids

    async def set_assignments(
        self,
        policy: Policy,
        is_global: bool,
        group_ids: list[UUID],
        agent_ids: list[UUID],
        assigned_by_id: UUID | None,
    ) -> None:
        policy.is_global = is_global

        await self._session.execute(
            delete(policy_group_assignments)
            .where(policy_group_assignments.c.policy_id == policy.id)
        )
        if group_ids:
            await self._session.execute(
                insert(policy_group_assignments),
                [{"policy_id": policy.id, "group_id": gid, "assigned_by_id": assigned_by_id}
                 for gid in group_ids],
            )

        await self._session.execute(
            delete(policy_agent_assignments)
            .where(policy_agent_assignments.c.policy_id == policy.id)
        )
        if agent_ids:
            await self._session.execute(
                insert(policy_agent_assignments),
                [{"policy_id": policy.id, "agent_id": aid, "assigned_by_id": assigned_by_id}
                 for aid in agent_ids],
            )

        await self._session.flush()

    async def get_for_group(self, group_id: UUID) -> list[Policy]:
        stmt = (
            select(Policy)
            .join(policy_group_assignments, policy_group_assignments.c.policy_id == Policy.id)
            .where(
                Policy.deleted_at.is_(None),
                policy_group_assignments.c.group_id == group_id,
            )
            .order_by(Policy.name)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def get_for_agent(self, agent_id: UUID) -> list[Policy]:
        from umbrella_server.domains.groups.models import agent_group_memberships

        stmt = (
            select(Policy)
            .where(
                Policy.deleted_at.is_(None),
                Policy.is_active.is_(True),
                or_(
                    Policy.is_global.is_(True),
                    Policy.id.in_(
                        select(policy_group_assignments.c.policy_id)
                        .join(
                            agent_group_memberships,
                            agent_group_memberships.c.group_id == policy_group_assignments.c.group_id,
                        )
                        .where(agent_group_memberships.c.agent_id == agent_id)
                    ),
                    Policy.id.in_(
                        select(policy_agent_assignments.c.policy_id)
                        .where(policy_agent_assignments.c.agent_id == agent_id)
                    ),
                ),
            )
            .order_by(Policy.name)
            .distinct()
        )
        result = await self._session.scalars(stmt)
        return list(result.all())
