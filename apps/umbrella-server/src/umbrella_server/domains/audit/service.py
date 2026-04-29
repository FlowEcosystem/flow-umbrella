from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.audit.models import AuditLog
from umbrella_server.domains.audit.repository import AuditRepository


class AuditService:
    def __init__(self, session: AsyncSession, repo: AuditRepository) -> None:
        self._session = session
        self._repo = repo

    async def log(
        self,
        action: str,
        *,
        entity_type: str | None = None,
        entity_id: str | None = None,
        details: dict | None = None,
        admin_id: UUID | None = None,
        admin_email: str | None = None,
    ) -> None:
        await self._repo.create(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            admin_id=admin_id,
            admin_email=admin_email,
        )
        await self._session.commit()

    async def list(
        self,
        *,
        action: str | None = None,
        entity_type: str | None = None,
        admin_email: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[AuditLog], int]:
        return await self._repo.list(
            action=action,
            entity_type=entity_type,
            admin_email=admin_email,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
            offset=offset,
        )
