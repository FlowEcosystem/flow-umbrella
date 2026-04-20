"""HTTP-роутер instance-домена."""

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends

from umbrella_server.domains.auth.dependencies import (
    current_any_admin,
    current_superadmin,
)
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.instance.schemas import InstanceRead, InstanceUpdate
from umbrella_server.domains.instance.service import InstanceService

instance_router = APIRouter(prefix="/v1/instance", tags=["instance"])


def _to_read(config) -> InstanceRead:
    return InstanceRead(
        branch_id=config.branch_id,
        branch_name=config.branch_name,
        hq_base_url=config.hq_base_url,
        hq_sync_enabled=config.hq_sync_enabled,
        hq_enrolled=config.hq_access_token is not None,
        hq_last_sync_at=config.hq_last_sync_at,
    )


@instance_router.get("", response_model=InstanceRead)
@inject
async def get_instance(
    _current: Annotated[Admin, Depends(current_any_admin)],
    service: FromDishka[InstanceService],
) -> InstanceRead:
    config = await service.get()
    return _to_read(config)


@instance_router.patch("", response_model=InstanceRead)
@inject
async def update_instance(
    payload: InstanceUpdate,
    _current: Annotated[Admin, Depends(current_superadmin)],
    service: FromDishka[InstanceService],
) -> InstanceRead:
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        config = await service.get()
    else:
        config = await service.update(fields)
    return _to_read(config)