"""Pydantic-схемы для релизов агентов."""

from datetime import datetime

from pydantic import BaseModel


class AgentReleaseRead(BaseModel):
    id: str          # filename — acts as stable identifier
    version: str
    platform: str
    arch: str
    filename: str
    file_size: int
    checksum: str
    uploaded_at: datetime
