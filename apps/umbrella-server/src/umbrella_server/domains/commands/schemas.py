"""Pydantic-схемы домена команд."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from umbrella_server.domains.commands.models import CommandStatus, CommandType


class CommandCreate(BaseModel):
    type: CommandType
    payload: dict | None = None
    expires_in_sec: int | None = None


class CommandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    type: CommandType
    status: CommandStatus
    payload: dict | None
    result: dict | None
    error_message: str | None
    issued_by_id: UUID | None
    sent_at: datetime | None
    acknowledged_at: datetime | None
    completed_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Agent-facing schemas
# ---------------------------------------------------------------------------

class AgentCommandItem(BaseModel):
    """Команда в очереди агента — минимальный набор полей."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: CommandType
    payload: dict | None
    expires_at: datetime | None


class AgentCommandResultRequest(BaseModel):
    status: CommandStatus
    result: dict | None = None
    error_message: str | None = None
