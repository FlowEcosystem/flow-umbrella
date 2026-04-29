from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    admin_id: UUID | None
    admin_email: str | None
    action: str
    entity_type: str | None
    entity_id: str | None
    details: dict | None
    created_at: datetime
