"""Сервис policies-домена."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.core.logging import get_logger
from umbrella_server.domains.policies.exceptions import (
    PolicyNameAlreadyExistsError,
    PolicyNotFoundError,
    PolicyReadOnlyError,
    ServiceNameAlreadyExistsError,
    ServiceNotFoundError,
    ServiceReadOnlyError,
)
from umbrella_server.domains.policies.models import Policy, PolicyAction, PolicyKind, PolicySource, Service
from umbrella_server.domains.policies.repository import PolicyRepository, ServiceRepository

logger = get_logger(__name__)


class ServiceService:
    def __init__(self, session: AsyncSession, repo: ServiceRepository) -> None:
        self._session = session
        self._repo = repo

    async def get(self, service_id: UUID) -> Service:
        service = await self._repo.get_by_id(service_id)
        if service is None:
            raise ServiceNotFoundError(service_id)
        return service

    async def get_by_ids(self, service_ids: list[UUID]) -> list[Service]:
        if not service_ids:
            return []
        services = await self._repo.get_by_ids(service_ids)
        found_ids = {s.id for s in services}
        for sid in service_ids:
            if sid not in found_ids:
                raise ServiceNotFoundError(sid)
        return services

    async def list(
        self, *, limit: int, offset: int,
        source: PolicySource | None = None,
        category: str | None = None,
        kind: PolicyKind | None = None,
    ) -> tuple[list[Service], int]:
        items = await self._repo.list(limit=limit, offset=offset, source=source, category=category, kind=kind)
        total = await self._repo.count(source=source, category=category, kind=kind)
        return items, total

    async def create(
        self, *, name: str, category: str, description: str | None,
        rules: list[dict], is_active: bool,
        kind: PolicyKind = PolicyKind.TRAFFIC,
    ) -> Service:
        existing = await self._repo.get_by_name(name)
        if existing is not None:
            raise ServiceNameAlreadyExistsError(name)
        service = await self._repo.create(
            name=name, category=category, description=description,
            rules=rules, is_active=is_active, kind=kind, source=PolicySource.LOCAL,
        )
        await self._session.commit()
        logger.info("service_created", service_id=service.id, name=name)
        return service

    async def update(self, service_id: UUID, fields: dict[str, Any]) -> Service:
        service = await self.get(service_id)
        if service.source == PolicySource.GLOBAL:
            raise ServiceReadOnlyError(service_id)
        if "name" in fields and fields["name"] != service.name:
            existing = await self._repo.get_by_name(fields["name"])
            if existing is not None:
                raise ServiceNameAlreadyExistsError(fields["name"])
        await self._repo.update(service, fields)
        await self._session.commit()
        logger.info("service_updated", service_id=service.id, fields=list(fields.keys()))
        return service

    async def delete(self, service_id: UUID) -> None:
        service = await self.get(service_id)
        if service.source == PolicySource.GLOBAL:
            raise ServiceReadOnlyError(service_id)
        await self._repo.soft_delete(service)
        await self._session.commit()
        logger.info("service_deleted", service_id=service.id)


class PolicyService:
    def __init__(
        self, session: AsyncSession, repo: PolicyRepository, service_repo: ServiceRepository,
    ) -> None:
        self._session = session
        self._repo = repo
        self._service_repo = service_repo

    async def get(self, policy_id: UUID) -> Policy:
        policy = await self._repo.get_by_id(policy_id)
        if policy is None:
            raise PolicyNotFoundError(policy_id)
        return policy

    async def list(
        self, *, limit: int, offset: int,
        source: PolicySource | None = None,
        action: PolicyAction | None = None,
        is_active: bool | None = None,
        kind: PolicyKind | None = None,
    ) -> tuple[list[Policy], int]:
        items = await self._repo.list(
            limit=limit, offset=offset, source=source, action=action, is_active=is_active, kind=kind,
        )
        total = await self._repo.count(source=source, action=action, is_active=is_active, kind=kind)
        return items, total

    async def create(
        self, *, name: str, description: str | None, action: PolicyAction,
        is_active: bool, service_ids: list[UUID], custom_rules: list[dict],
        kind: PolicyKind = PolicyKind.TRAFFIC,
    ) -> Policy:
        existing = await self._repo.get_by_name(name)
        if existing is not None:
            raise PolicyNameAlreadyExistsError(name)
        services = await self._service_repo.get_by_ids(service_ids)
        policy = await self._repo.create(
            name=name, description=description, action=action,
            is_active=is_active, custom_rules=custom_rules,
            kind=kind, services=services, source=PolicySource.LOCAL,
        )
        await self._session.commit()
        logger.info("policy_created", policy_id=policy.id, name=name)
        return policy

    async def update(self, policy_id: UUID, fields: dict[str, Any]) -> Policy:
        policy = await self.get(policy_id)
        if policy.source == PolicySource.GLOBAL:
            raise PolicyReadOnlyError(policy_id)

        services = None
        if "service_ids" in fields:
            service_ids = fields.pop("service_ids")
            if service_ids is not None:
                services = await self._service_repo.get_by_ids(service_ids)

        if "name" in fields and fields["name"] != policy.name:
            existing = await self._repo.get_by_name(fields["name"])
            if existing is not None:
                raise PolicyNameAlreadyExistsError(fields["name"])

        await self._repo.update(policy, fields, services=services)
        await self._session.commit()
        logger.info("policy_updated", policy_id=policy.id, fields=list(fields.keys()))
        return policy

    async def delete(self, policy_id: UUID) -> None:
        policy = await self.get(policy_id)
        if policy.source == PolicySource.GLOBAL:
            raise PolicyReadOnlyError(policy_id)
        await self._repo.soft_delete(policy)
        await self._session.commit()
        logger.info("policy_deleted", policy_id=policy.id)

    async def assign(
        self,
        policy_id: UUID,
        is_global: bool,
        group_ids: list[UUID],
        agent_ids: list[UUID],
        assigned_by_id: UUID | None,
    ) -> None:
        policy = await self.get(policy_id)
        await self._repo.set_assignments(
            policy,
            is_global=is_global,
            group_ids=group_ids,
            agent_ids=agent_ids,
            assigned_by_id=assigned_by_id,
        )
        await self._session.commit()
        logger.info(
            "policy_assigned", policy_id=policy_id,
            is_global=is_global, groups=len(group_ids), agents=len(agent_ids),
        )

    async def get_assignments_detail(self, policy_id: UUID) -> dict:
        await self.get(policy_id)
        is_global, group_ids, agent_ids = await self._repo.get_assignments(policy_id)

        groups: list[dict] = []
        if group_ids:
            from umbrella_server.domains.groups.models import Group
            result = await self._session.scalars(
                select(Group)
                .where(Group.id.in_(group_ids), Group.deleted_at.is_(None))
            )
            groups = [{"group_id": g.id, "name": g.name, "color": g.color}
                      for g in result.all()]

        agents: list[dict] = []
        if agent_ids:
            from umbrella_server.domains.agents.models import Agent
            result = await self._session.scalars(
                select(Agent)
                .where(Agent.id.in_(agent_ids), Agent.deleted_at.is_(None))
            )
            agents = [{"agent_id": a.id, "hostname": a.hostname} for a in result.all()]

        return {"is_global": is_global, "groups": groups, "agents": agents}

    async def get_policies_for_agent(self, agent_id: UUID) -> list[Policy]:
        return await self._repo.get_for_agent(agent_id)

    async def get_policies_for_group(self, group_id: UUID) -> list[Policy]:
        return await self._repo.get_for_group(group_id)
