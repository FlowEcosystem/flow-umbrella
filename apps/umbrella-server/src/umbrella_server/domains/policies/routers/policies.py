"""Роутер политик: /v1/policies/*."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, status

from umbrella_server.core.pagination import Page, PaginationMeta, PaginationParams
from umbrella_server.domains.auth.dependencies import require_capability
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.policies.models import PolicyAction, PolicyKind, PolicySource
from umbrella_server.domains.policies.schemas import (
    PolicyAssignmentsRead, PolicyAssignRequest, PolicyCreate, PolicyRead, PolicyUpdate, ServiceRead,
)
from umbrella_server.domains.policies.service import PolicyService

policies_router = APIRouter(prefix="/v1/policies", tags=["policies"])


def _service_to_read(service) -> ServiceRead:
    return ServiceRead(
        id=service.id,
        name=service.name,
        category=service.category,
        description=service.description,
        kind=service.kind,
        source=service.source,
        is_active=service.is_active,
        rules=service.rules or [],
        rules_count=len(service.rules or []),
        created_at=service.created_at,
        updated_at=service.updated_at,
    )


def _to_read(policy) -> PolicyRead:
    services = [_service_to_read(s) for s in (policy.services or [])]
    custom_rules = policy.custom_rules or []
    service_rules_count = sum(len(s.rules or []) for s in (policy.services or []))
    return PolicyRead(
        id=policy.id,
        name=policy.name,
        description=policy.description,
        kind=policy.kind,
        source=policy.source,
        action=policy.action,
        is_active=policy.is_active,
        is_global=policy.is_global,
        overridable=policy.overridable,
        version=policy.version,
        hq_policy_id=policy.hq_policy_id,
        services=services,
        custom_rules=custom_rules,
        rules_count=service_rules_count + len(custom_rules),
        created_at=policy.created_at,
        updated_at=policy.updated_at,
    )


@policies_router.get("", response_model=Page[PolicyRead])
@inject
async def list_policies(
    _current: Annotated[Admin, Depends(require_capability("policies:read"))],
    pagination: Annotated[PaginationParams, Depends()],
    service: FromDishka[PolicyService],
    source: PolicySource | None = None,
    action: PolicyAction | None = None,
    is_active: bool | None = None,
    kind: PolicyKind | None = None,
) -> Page[PolicyRead]:
    items, total = await service.list(
        limit=pagination.limit, offset=pagination.offset,
        source=source, action=action, is_active=is_active, kind=kind,
    )
    return Page[PolicyRead](
        items=[_to_read(p) for p in items],
        meta=PaginationMeta(total=total, limit=pagination.limit, offset=pagination.offset),
    )


@policies_router.post("", response_model=PolicyRead, status_code=status.HTTP_201_CREATED)
@inject
async def create_policy(
    payload: PolicyCreate,
    _current: Annotated[Admin, Depends(require_capability("policies:write"))],
    service: FromDishka[PolicyService],
) -> PolicyRead:
    policy = await service.create(
        name=payload.name,
        description=payload.description,
        action=payload.action,
        is_active=payload.is_active,
        kind=payload.kind,
        service_ids=payload.service_ids,
        custom_rules=[r.model_dump() for r in payload.custom_rules],
    )
    return _to_read(policy)


@policies_router.get("/{policy_id}", response_model=PolicyRead)
@inject
async def get_policy(
    policy_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("policies:read"))],
    service: FromDishka[PolicyService],
) -> PolicyRead:
    policy = await service.get(policy_id)
    return _to_read(policy)


@policies_router.patch("/{policy_id}", response_model=PolicyRead)
@inject
async def update_policy(
    policy_id: UUID,
    payload: PolicyUpdate,
    _current: Annotated[Admin, Depends(require_capability("policies:write"))],
    service: FromDishka[PolicyService],
) -> PolicyRead:
    fields = payload.model_dump(exclude_unset=True)
    if "custom_rules" in fields and fields["custom_rules"] is not None:
        fields["custom_rules"] = [
            r.model_dump() if hasattr(r, "model_dump") else r
            for r in fields["custom_rules"]
        ]
    if fields:
        policy = await service.update(policy_id, fields)
    else:
        policy = await service.get(policy_id)
    return _to_read(policy)


@policies_router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_policy(
    policy_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("policies:write"))],
    service: FromDishka[PolicyService],
) -> None:
    await service.delete(policy_id)


@policies_router.post("/{policy_id}/assign", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def assign_policy(
    policy_id: UUID,
    payload: PolicyAssignRequest,
    current: Annotated[Admin, Depends(require_capability("policies:write"))],
    service: FromDishka[PolicyService],
) -> None:
    await service.assign(
        policy_id,
        is_global=payload.is_global,
        group_ids=payload.group_ids,
        agent_ids=payload.agent_ids,
        assigned_by_id=current.id,
    )


@policies_router.get("/{policy_id}/assignments", response_model=PolicyAssignmentsRead)
@inject
async def get_policy_assignments(
    policy_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("policies:read"))],
    service: FromDishka[PolicyService],
) -> PolicyAssignmentsRead:
    data = await service.get_assignments_detail(policy_id)
    return PolicyAssignmentsRead(**data)
