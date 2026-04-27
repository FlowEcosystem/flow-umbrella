"""Админский API агентов и enrollment-токенов."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, HTTPException, status

from umbrella_server.core.pagination import Page, PaginationMeta, PaginationParams
from umbrella_server.domains.agents.schemas import (
    AgentDecommissionTokenResponse,
    AgentFilter,
    AgentRead,
    AgentUpdate,
    EnrollmentTokenCreate,
    EnrollmentTokenCreated,
    EnrollmentTokenRead,
)
from umbrella_server.domains.agents.service import AgentService
from umbrella_server.domains.auth.dependencies import current_any_admin, require_capability
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.groups.schemas import GroupRead
from umbrella_server.domains.groups.service import GroupService
from umbrella_server.domains.policies.schemas import EffectivePolicyItem
from umbrella_server.domains.policies.service import PolicyService

agents_router = APIRouter(prefix="/v1/agents", tags=["agents"])
enrollment_tokens_router = APIRouter(prefix="/v1/enrollment-tokens", tags=["enrollment-tokens"])


# ── Enrollment tokens ────────────────────────────────────────────────────────

@enrollment_tokens_router.post(
    "", response_model=EnrollmentTokenCreated, status_code=status.HTTP_201_CREATED
)
@inject
async def create_enrollment_token(
    payload: EnrollmentTokenCreate,
    current: Annotated[Admin, Depends(require_capability("agents:write"))],
    service: FromDishka[AgentService],
) -> EnrollmentTokenCreated:
    token, raw = await service.create_enrollment_token(
        note=payload.note,
        expires_in_days=payload.expires_in_days,
        group_id=payload.group_id,
        max_uses=payload.max_uses,
        created_by_id=current.id,
    )
    return EnrollmentTokenCreated(
        token=EnrollmentTokenRead.model_validate(token),
        raw_token=raw,
    )


@enrollment_tokens_router.get("", response_model=list[EnrollmentTokenRead])
@inject
async def list_enrollment_tokens(
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    service: FromDishka[AgentService],
) -> list[EnrollmentTokenRead]:
    tokens = await service.list_enrollment_tokens()
    return [EnrollmentTokenRead.model_validate(t) for t in tokens]


@enrollment_tokens_router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def revoke_enrollment_token(
    token_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:write"))],
    service: FromDishka[AgentService],
) -> None:
    await service.revoke_enrollment_token(token_id)


# ── Agents ───────────────────────────────────────────────────────────────────

@agents_router.get("", response_model=Page[AgentRead])
@inject
async def list_agents(
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    pagination: Annotated[PaginationParams, Depends()],
    filters: Annotated[AgentFilter, Depends()],
    service: FromDishka[AgentService],
) -> Page[AgentRead]:
    items, total = await service.list(
        limit=pagination.limit,
        offset=pagination.offset,
        statuses=filters.status,
        os=filters.os,
        search=filters.search,
    )
    return Page[AgentRead](
        items=[AgentRead.model_validate(a) for a in items],
        meta=PaginationMeta(total=total, limit=pagination.limit, offset=pagination.offset),
    )


@agents_router.get("/{agent_id}", response_model=AgentRead)
@inject
async def get_agent(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    service: FromDishka[AgentService],
) -> AgentRead:
    return AgentRead.model_validate(await service.get(agent_id))


@agents_router.patch("/{agent_id}", response_model=AgentRead)
@inject
async def update_agent(
    agent_id: UUID,
    payload: AgentUpdate,
    _current: Annotated[Admin, Depends(require_capability("agents:write"))],
    service: FromDishka[AgentService],
) -> AgentRead:
    fields = payload.model_dump(exclude_unset=True)
    agent = await service.update(agent_id, fields) if fields else await service.get(agent_id)
    return AgentRead.model_validate(agent)


@agents_router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_agent(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:write"))],
    service: FromDishka[AgentService],
) -> None:
    try:
        await service.delete(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@agents_router.get("/{agent_id}/groups", response_model=list[GroupRead])
@inject
async def list_agent_groups(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    group_service: FromDishka[GroupService],
) -> list[GroupRead]:
    groups, counts = await group_service.list_groups_for_agent(agent_id)
    return [
        GroupRead(
            id=g.id, name=g.name, description=g.description, color=g.color,
            agents_count=counts.get(g.id, 0), created_at=g.created_at, updated_at=g.updated_at,
        )
        for g in groups
    ]


@agents_router.get("/{agent_id}/policies", response_model=list[EffectivePolicyItem])
@inject
async def list_agent_policies(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    policy_service: FromDishka[PolicyService],
) -> list[EffectivePolicyItem]:
    policies = await policy_service.get_policies_for_agent(agent_id)
    result = []
    for p in policies:
        service_rules_count = sum(len(s.rules or []) for s in (p.services or []))
        result.append(EffectivePolicyItem(
            id=p.id, name=p.name, kind=p.kind, action=p.action,
            is_active=p.is_active, is_global=p.is_global, version=p.version,
            rules_count=service_rules_count + len(p.custom_rules or []),
        ))
    return result


@agents_router.post(
    "/{agent_id}/decommission-token",
    response_model=AgentDecommissionTokenResponse,
)
@inject
async def get_decommission_token(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:write"))],
    service: FromDishka[AgentService],
) -> AgentDecommissionTokenResponse:
    agent = await service.get(agent_id)
    token, expires_at = service.generate_decommission_token(agent)
    return AgentDecommissionTokenResponse(token=token, expires_at=expires_at)
