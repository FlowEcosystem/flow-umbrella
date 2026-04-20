"""Админский CRUD агентов: /v1/agents/*."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, status

from umbrella_server.core.pagination import Page, PaginationMeta, PaginationParams
from umbrella_server.domains.agents.schemas import (
    AgentCreate,
    AgentCreateResponse,
    AgentFilter,
    AgentRead,
    AgentUpdate,
)
from umbrella_server.domains.agents.service import AgentService
from umbrella_server.domains.auth.dependencies import require_capability
from umbrella_server.domains.auth.models import Admin

agents_router = APIRouter(prefix="/v1/agents", tags=["agents"])


@agents_router.post(
    "", response_model=AgentCreateResponse, status_code=status.HTTP_201_CREATED
)
@inject
async def create_agent(
    payload: AgentCreate,
    _current: Annotated[Admin, Depends(require_capability("agents:write"))],
    service: FromDishka[AgentService],
) -> AgentCreateResponse:
    agent, raw_token = await service.create(
        hostname=payload.hostname,
        os=payload.os,
        notes=payload.notes,
    )
    return AgentCreateResponse(
        agent=AgentRead.model_validate(agent),
        enrollment_token=raw_token,
        enrollment_token_expires_at=agent.enrollment_token_expires_at, # pyright: ignore[reportArgumentType]
    )


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
        meta=PaginationMeta(
            total=total, limit=pagination.limit, offset=pagination.offset
        ),
    )


@agents_router.get("/{agent_id}", response_model=AgentRead)
@inject
async def get_agent(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    service: FromDishka[AgentService],
) -> AgentRead:
    agent = await service.get(agent_id)
    return AgentRead.model_validate(agent)


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
    await service.delete(agent_id)


@agents_router.post(
    "/{agent_id}/regenerate-enrollment-token",
    response_model=AgentCreateResponse,
)
@inject
async def regenerate_enrollment_token(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:write"))],
    service: FromDishka[AgentService],
) -> AgentCreateResponse:
    agent, raw_token = await service.regenerate_enrollment_token(agent_id)
    return AgentCreateResponse(
        agent=AgentRead.model_validate(agent),
        enrollment_token=raw_token,
        enrollment_token_expires_at=agent.enrollment_token_expires_at, # pyright: ignore[reportArgumentType]
    )