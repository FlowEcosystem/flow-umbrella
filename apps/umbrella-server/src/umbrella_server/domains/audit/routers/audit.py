from datetime import datetime
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends

from umbrella_server.core.pagination import Page, PaginationMeta, PaginationParams
from umbrella_server.domains.audit.schemas import AuditLogRead
from umbrella_server.domains.audit.service import AuditService
from umbrella_server.domains.auth.dependencies import require_capability
from umbrella_server.domains.auth.models import Admin

audit_router = APIRouter(prefix="/v1/audit-log", tags=["audit"])


@audit_router.get("", response_model=Page[AuditLogRead])
@inject
async def list_audit_log(
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    pagination: Annotated[PaginationParams, Depends()],
    action: str | None = None,
    entity_type: str | None = None,
    admin_email: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    service: FromDishka[AuditService] = ...,
) -> Page[AuditLogRead]:
    items, total = await service.list(
        action=action,
        entity_type=entity_type,
        admin_email=admin_email,
        date_from=date_from,
        date_to=date_to,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return Page[AuditLogRead](
        items=[AuditLogRead.model_validate(e) for e in items],
        meta=PaginationMeta(total=total, limit=pagination.limit, offset=pagination.offset),
    )
