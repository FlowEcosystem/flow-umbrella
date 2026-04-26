"""Pydantic-схемы домена метрик."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentMetricPush(BaseModel):
    collected_at: datetime
    cpu_percent: float | None = Field(default=None, ge=0, le=100)
    ram_used_mb: int | None = Field(default=None, ge=0)
    ram_total_mb: int | None = Field(default=None, ge=0)
    disk_used_gb: float | None = Field(default=None, ge=0)
    disk_total_gb: float | None = Field(default=None, ge=0)


class AgentMetricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    collected_at: datetime
    cpu_percent: float | None
    ram_used_mb: int | None
    ram_total_mb: int | None
    disk_used_gb: float | None
    disk_total_gb: float | None
