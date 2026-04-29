"""Админский API команд: /v1/agents/{agent_id}/commands/*."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, status

from umbrella_server.domains.audit.service import AuditService
from umbrella_server.domains.auth.dependencies import require_capability
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.commands.schemas import CommandCreate, CommandRead
from umbrella_server.domains.commands.service import CommandService

commands_router = APIRouter(prefix="/v1/agents/{agent_id}/commands", tags=["commands"])


@commands_router.post("", response_model=CommandRead, status_code=status.HTTP_201_CREATED)
@inject
async def issue_command(
    agent_id: UUID,
    payload: CommandCreate,
    _current: Annotated[Admin, Depends(require_capability("commands:write"))],
    service: FromDishka[CommandService],
    audit: FromDishka[AuditService],
) -> CommandRead:
    cmd = await service.issue(
        agent_id=agent_id,
        type=payload.type,
        payload=payload.payload,
        issued_by_id=_current.id,
        expires_in_sec=payload.expires_in_sec,
    )
    await audit.log(
        "command.issued",
        entity_type="command",
        entity_id=str(cmd.id),
        details={"command_type": payload.type.value, "agent_id": str(agent_id), "payload": payload.payload},
        admin_id=_current.id,
        admin_email=_current.email,
    )
    return CommandRead.model_validate(cmd)


@commands_router.get("", response_model=list[CommandRead])
@inject
async def list_commands(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("commands:read"))],
    service: FromDishka[CommandService],
) -> list[CommandRead]:
    cmds = await service.list_for_agent(agent_id)
    return [CommandRead.model_validate(c) for c in cmds]


@commands_router.get("/{command_id}", response_model=CommandRead)
@inject
async def get_command(
    agent_id: UUID,
    command_id: UUID,
    _current: Annotated[Admin, Depends(require_capability("commands:read"))],
    service: FromDishka[CommandService],
) -> CommandRead:
    cmd = await service.get(command_id)
    return CommandRead.model_validate(cmd)
