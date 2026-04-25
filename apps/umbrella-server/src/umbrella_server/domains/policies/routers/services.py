"""Роутер сервисов: /v1/services/*."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, status

from umbrella_server.core.pagination import Page, PaginationMeta, PaginationParams
from umbrella_server.domains.auth.dependencies import require_capability
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.policies.models import PolicyKind, PolicySource
from umbrella_server.domains.policies.schemas import ServiceCreate, ServiceRead, ServiceUpdate
from umbrella_server.domains.policies.service import ServiceService

services_router = APIRouter(prefix="/v1/services", tags=["services"])


def _to_read(service) -> ServiceRead:
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


@services_router.get("", response_model=Page[ServiceRead])
@inject
async def list_services(
    _current: Annotated[Admin, Depends(require_capability("policies:read"))],
    pagination: Annotated[PaginationParams, Depends()],
    svc: FromDishka[ServiceService],
    source: PolicySource | None = None,
    category: str | None = None,
    kind: PolicyKind | None = None,
) -> Page[ServiceRead]:
    items, total = await svc.list(
        limit=pagination.limit, offset=pagination.offset,
        source=source, category=category, kind=kind,
    )
    return Page[ServiceRead](
        items=[_to_read(s) for s in items],
        meta=PaginationMeta(total=total, limit=pagination.limit, offset=pagination.offset),
    )


@services_router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
@inject
async def create_service(
    payload: ServiceCreate,
    _current: Annotated[Admin, Depends(require_capability("policies:write"))],
    svc: FromDishka[ServiceService],
) -> ServiceRead:
    service = await svc.create(
        name=payload.name,
        category=payload.category,
        description=payload.description,
        kind=payload.kind,
        rules=[r.model_dump() for r in payload.rules],
        is_active=payload.is_active,
    )
    return _to_read(service)


@services_router.get("/{service_id}", response_model=ServiceRead)
@inject
async def get_service(
    service_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("policies:read"))],
    svc: FromDishka[ServiceService],
) -> ServiceRead:
    service = await svc.get(service_id)
    return _to_read(service)


@services_router.patch("/{service_id}", response_model=ServiceRead)
@inject
async def update_service(
    service_id: UUID,
    payload: ServiceUpdate,
    _current: Annotated[Admin, Depends(require_capability("policies:write"))],
    svc: FromDishka[ServiceService],
) -> ServiceRead:
    fields = payload.model_dump(exclude_unset=True)
    if "rules" in fields and fields["rules"] is not None:
        fields["rules"] = [
            r.model_dump() if hasattr(r, "model_dump") else r
            for r in fields["rules"]
        ]
    service = await svc.update(service_id, fields) if fields else await svc.get(service_id)
    return _to_read(service)


@services_router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_service(
    service_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("policies:write"))],
    svc: FromDishka[ServiceService],
) -> None:
    await svc.delete(service_id)
