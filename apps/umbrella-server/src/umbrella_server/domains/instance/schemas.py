"""Pydantic-схемы instance-домена."""

from datetime import datetime
from uuid import UUID

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field


class InstanceRead(BaseModel):
    """Публичное представление конфига филиала.

    Токены (enrollment, access) наружу НЕ отдаём — это секреты.
    """
    model_config = ConfigDict(from_attributes=True)

    branch_id: UUID
    branch_name: str
    hq_base_url: str | None
    hq_sync_enabled: bool
    hq_enrolled: bool
    hq_last_sync_at: datetime | None


class InstanceUpdate(BaseModel):
    """Редактируемые админом поля.

    branch_id НЕ редактируем никогда (identity филиала).
    HQ-токены ставятся через enrollment-flow, не через этот PATCH.
    """
    branch_name: str | None = Field(default=None, min_length=1, max_length=255)
    hq_base_url: AnyHttpUrl | None = None
    hq_sync_enabled: bool | None = None