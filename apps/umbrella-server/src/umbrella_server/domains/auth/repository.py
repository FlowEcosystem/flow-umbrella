"""Репозитории auth-домена: AdminRepository, RefreshTokenRepository.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Select, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from umbrella_server.domains.auth.models import Admin, AdminRole, RefreshToken


class AdminRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _active_admins(self) -> Select[tuple[Admin]]:
        return select(Admin).where(Admin.deleted_at.is_(None))

    async def get_by_id(self, admin_id: UUID) -> Admin | None:
        stmt = self._active_admins().where(Admin.id == admin_id)
        return await self._session.scalar(stmt)

    async def get_by_email(self, email: str) -> Admin | None:
        stmt = self._active_admins().where(Admin.email == email)
        return await self._session.scalar(stmt)

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        role: AdminRole,
        full_name: str | None = None,
        is_active: bool = True,
    ) -> Admin:
        admin = Admin(
            email=email,
            password_hash=password_hash,
            role=role,
            full_name=full_name,
            is_active=is_active,
        )
        self._session.add(admin)
        await self._session.flush()
        return admin

    async def update(self, admin: Admin, fields: dict) -> Admin:
        for key, value in fields.items():
            setattr(admin, key, value)
        await self._session.flush()
        return admin

    async def soft_delete(self, admin: Admin) -> None:
        admin.deleted_at = datetime.now(UTC)
        await self._session.flush()

    async def update_last_login(self, admin: Admin) -> None:
        admin.last_login_at = datetime.now(UTC)
        await self._session.flush()

    async def list(self, *, limit: int, offset: int) -> list[Admin]:
        stmt = (
            self._active_admins()
            .order_by(Admin.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.scalars(stmt)
        return list(result.all())

    async def count(self) -> int:
        stmt = select(func.count()).select_from(Admin).where(Admin.deleted_at.is_(None))
        return await self._session.scalar(stmt) or 0


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        admin_id: UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        token = RefreshToken(
            admin_id=admin_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_by_hash(self, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return await self._session.scalar(stmt)

    async def revoke(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(UTC)
        await self._session.flush()

    async def revoke_all_for_admin(self, admin_id: UUID) -> int:
        """Отзывает все активные токены админа. Возвращает количество."""
        now = datetime.now(UTC)
        stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.admin_id == admin_id,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        result = await self._session.execute(stmt)
        return result.rowcount # pyright: ignore[reportAttributeAccessIssue]

    async def delete_expired(self) -> int:
        """Физически удаляет просроченные токены. Для cron-задачи."""
        now = datetime.now(UTC)
        stmt = delete(RefreshToken).where(RefreshToken.expires_at < now)
        result = await self._session.execute(stmt)
        return result.rowcount # pyright: ignore[reportAttributeAccessIssue]