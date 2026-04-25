"""Админский CRUD групп: /v1/groups/*."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, status

from umbrella_server.core.pagination import Page, PaginationMeta, PaginationParams
from umbrella_server.domains.agents.schemas import AgentRead
from umbrella_server.domains.groups.schemas import (
    GroupAddAgents,
    GroupAddAgentsResponse,
    GroupCreate,
    GroupRead,
    GroupUpdate,
)
from umbrella_server.domains.groups.service import GroupService
from umbrella_server.domains.auth.dependencies import require_capability
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.policies.schemas import EffectivePolicyItem
from umbrella_server.domains.policies.service import PolicyService

groups_router = APIRouter(prefix="/v1/groups", tags=["groups"])


def _to_read(group, agents_count: int) -> GroupRead:
    return GroupRead(
        id=group.id,
        name=group.name,
        description=group.description,
        color=group.color,
        agents_count=agents_count,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@groups_router.post(
    "", response_model=GroupRead, status_code=status.HTTP_201_CREATED
)
@inject
async def create_group(
    payload: GroupCreate,
    _current: Annotated[Admin, Depends(require_capability("groups:write"))],
    service: FromDishka[GroupService],
) -> GroupRead:
    group = await service.create(
        name=payload.name,
        description=payload.description,
        color=payload.color,
    )
    return _to_read(group, agents_count=0)


@groups_router.get("", response_model=Page[GroupRead])
@inject
async def list_groups(
    _current: Annotated[Admin, Depends(require_capability("groups:read"))],
    pagination: Annotated[PaginationParams, Depends()],
    service: FromDishka[GroupService],
) -> Page[GroupRead]:
    items, counts, total = await service.list(
        limit=pagination.limit, offset=pagination.offset
    )
    return Page[GroupRead](
        items=[_to_read(g, counts.get(g.id, 0)) for g in items],
        meta=PaginationMeta(
            total=total, limit=pagination.limit, offset=pagination.offset
        ),
    )


@groups_router.get("/{group_id}", response_model=GroupRead)
@inject
async def get_group(
    group_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("groups:read"))],
    service: FromDishka[GroupService],
) -> GroupRead:
    group = await service.get(group_id)
    agents_count = await service.count_agents(group.id)
    return _to_read(group, agents_count)


@groups_router.patch("/{group_id}", response_model=GroupRead)
@inject
async def update_group(
    group_id: UUID,
    payload: GroupUpdate,
    _current: Annotated[Admin, Depends(require_capability("groups:write"))],
    service: FromDishka[GroupService],
) -> GroupRead:
    fields = payload.model_dump(exclude_unset=True)
    if fields:
        group = await service.update(group_id, fields)
    else:
        group = await service.get(group_id)
    agents_count = await service.count_agents(group.id)
    return _to_read(group, agents_count)


@groups_router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_group(
    group_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("groups:write"))],
    service: FromDishka[GroupService],
) -> None:
    await service.delete(group_id)


@groups_router.get("/{group_id}/agents", response_model=Page[AgentRead])
@inject
async def list_group_agents(
    group_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("groups:read"))],
    pagination: Annotated[PaginationParams, Depends()],
    service: FromDishka[GroupService],
) -> Page[AgentRead]:
    items, total = await service.list_agents(
        group_id, limit=pagination.limit, offset=pagination.offset
    )
    return Page[AgentRead](
        items=[AgentRead.model_validate(a) for a in items],
        meta=PaginationMeta(
            total=total, limit=pagination.limit, offset=pagination.offset
        ),
    )


@groups_router.post(
    "/{group_id}/agents",
    response_model=GroupAddAgentsResponse,
    status_code=status.HTTP_200_OK,
)
@inject
async def add_agents_to_group(
    group_id: UUID,
    payload: GroupAddAgents,
    _current: Annotated[Admin, Depends(require_capability("groups:write"))],
    service: FromDishka[GroupService],
) -> GroupAddAgentsResponse:
    added, already = await service.add_agents(group_id, payload.agent_ids)
    return GroupAddAgentsResponse(added=added, already_in_group=already)


@groups_router.delete(
    "/{group_id}/agents/{agent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
@inject
async def remove_agent_from_group(
    group_id: UUID,
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("groups:write"))],
    service: FromDishka[GroupService],
) -> None:
    await service.remove_agent(group_id, agent_id)


@groups_router.get("/{group_id}/policies", response_model=list[EffectivePolicyItem])
@inject
async def list_group_policies(
    group_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("groups:read"))],
    policy_service: FromDishka[PolicyService],
) -> list[EffectivePolicyItem]:
    policies = await policy_service.get_policies_for_group(group_id)
    result = []
    for p in policies:
        service_rules_count = sum(len(s.rules or []) for s in (p.services or []))
        result.append(EffectivePolicyItem(
            id=p.id,
            name=p.name,
            kind=p.kind,
            action=p.action,
            is_active=p.is_active,
            is_global=p.is_global,
            version=p.version,
            rules_count=service_rules_count + len(p.custom_rules or []),
        ))
    return result