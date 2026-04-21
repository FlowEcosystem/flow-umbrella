"""Pydantic-схемы groups-домена."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Hex-цвет в формате #RRGGBB. Простая валидация без regex-монстра.
def _validate_hex_color(v: str | None) -> str | None:
    if v is None:
        return v
    if not v.startswith("#") or len(v) != 7:
        raise ValueError("color must be a hex code like '#4338ca'")
    try:
        int(v[1:], 16)
    except ValueError as e:
        raise ValueError("color must be a hex code like '#4338ca'") from e
    return v.lower()


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    color: str | None = None

    @field_validator("color")
    @classmethod
    def _check_color(cls, v: str | None) -> str | None:
        return _validate_hex_color(v)


class GroupUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    color: str | None = None

    @field_validator("color")
    @classmethod
    def _check_color(cls, v: str | None) -> str | None:
        return _validate_hex_color(v)


class GroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    color: str | None
    agents_count: int
    created_at: datetime
    updated_at: datetime


class GroupAddAgents(BaseModel):
    agent_ids: list[UUID] = Field(min_length=1, max_length=500)


class GroupAddAgentsResponse(BaseModel):
    added: int
    already_in_group: int