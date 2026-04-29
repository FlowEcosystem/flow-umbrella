"""Админский API процессов агентов."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Query

from umbrella_server.domains.auth.dependencies import require_capability
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.processes.schemas import (
    GlobalProcessStatRead,
    ProcessSnapshotRead,
    ProcessStatRead,
)
from umbrella_server.domains.processes.service import ProcessService

processes_router = APIRouter(prefix="/v1", tags=["processes"])


@processes_router.get(
    "/agents/{agent_id}/processes",
    response_model=ProcessSnapshotRead | None,
)
@inject
async def get_agent_processes(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    service: FromDishka[ProcessService],
) -> ProcessSnapshotRead | None:
    snap = await service.get_latest(agent_id)
    if snap is None:
        return None
    return ProcessSnapshotRead.model_validate(snap)


@processes_router.get(
    "/agents/{agent_id}/process-stats",
    response_model=list[ProcessStatRead],
)
@inject
async def get_agent_process_stats(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    service: FromDishka[ProcessService],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ProcessStatRead]:
    stats = await service.get_stats(agent_id, limit)
    return [ProcessStatRead.model_validate(s) for s in stats]


@processes_router.get(
    "/process-stats",
    response_model=list[GlobalProcessStatRead],
)
@inject
async def get_global_process_stats(
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    service: FromDishka[ProcessService],
    limit: int = Query(default=20, ge=1, le=100),
) -> list[GlobalProcessStatRead]:
    stats = await service.get_global_stats(limit)
    return [GlobalProcessStatRead(**s) for s in stats]
