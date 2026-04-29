"""Pydantic-схемы домена процессов."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProcessItem(BaseModel):
    name: str
    pid: int
    cpu_percent: float = Field(default=0.0, ge=0)
    mem_mb: int = Field(default=0, ge=0)


class AgentProcessPush(BaseModel):
    collected_at: datetime
    processes: list[ProcessItem] = Field(default_factory=list)


class ProcessSnapshotRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    collected_at: datetime
    processes: list[ProcessItem]


class ProcessStatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    process_name: str
    seen_count: int
    first_seen_at: datetime
    last_seen_at: datetime


class GlobalProcessStatRead(BaseModel):
    process_name: str
    total_seen: int
    agent_count: int
