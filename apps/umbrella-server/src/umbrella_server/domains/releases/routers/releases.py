"""Эндпоинты управления релизами агентов."""

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import FileResponse

from umbrella_server.domains.agents.dependencies import current_agent
from umbrella_server.domains.agents.models import Agent
from umbrella_server.domains.auth.dependencies import require_capability
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.releases.schemas import AgentReleaseRead
from umbrella_server.domains.releases.service import ReleasesService

admin_releases_router = APIRouter(prefix="/v1/admin/releases", tags=["releases"])
agent_releases_router = APIRouter(prefix="/v1/releases", tags=["releases"])


@admin_releases_router.get("", response_model=list[AgentReleaseRead])
@inject
async def list_releases(
    _current: Annotated[Admin, Depends(require_capability("agents:read"))],
    service: FromDishka[ReleasesService],
    platform: Annotated[str | None, Query()] = None,
) -> list[AgentReleaseRead]:
    return service.list(platform=platform)


@admin_releases_router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_release(
    release_id: str,
    _current: Annotated[Admin, Depends(require_capability("agents:write"))],
    service: FromDishka[ReleasesService],
) -> None:
    service.delete(release_id)


@agent_releases_router.get("/{release_id}/download")
@inject
async def download_release(
    release_id: str,
    _agent: Annotated[Agent, Depends(current_agent)],
    service: FromDishka[ReleasesService],
) -> FileResponse:
    release = service.get(release_id)
    path = service.file_path(release)
    return FileResponse(
        path=str(path),
        filename=release.filename,
        media_type="application/octet-stream",
    )
