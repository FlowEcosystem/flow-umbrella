"""Сервисы auth-домена: AuthService (login/refresh/logout), AdminService (CRUD).

Commit транзакций — здесь. Rollback при исключении — в DI-провайдере session.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from umbrella_server.core.config import Settings
from umbrella_server.core.logging import get_logger
from umbrella_server.core.exceptions import ConflictError
from umbrella_server.domains.auth.exceptions import (
    AdminEmailAlreadyExistsError,
    AdminInactiveError,
    AdminNotFoundError,
    InvalidCredentialsError,
    RefreshTokenRevokedError,
    TokenExpiredError,
    TokenInvalidError,
)

from umbrella_server.domains.auth.models import Admin, AdminRole
from umbrella_server.domains.auth.repository import (
    AdminRepository,
    RefreshTokenRepository,
)
from umbrella_server.domains.auth.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_refresh_token,
    refresh_token_expires_at,
    verify_password,
)

logger = get_logger(__name__)


# Фиктивный bcrypt-hash для защиты от timing attack при несуществующем email.
_DUMMY_BCRYPT_HASH = "$2b$12$KIXQKXvQ7nwqkBbH.YFT5e.Wl.5jhRZ1Y8BvN8TqD/Y5Qg9FVb7uG"


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        admins: AdminRepository,
        tokens: RefreshTokenRepository,
    ) -> None:
        self._session = session
        self._settings = settings
        self._admins = admins
        self._tokens = tokens

    async def login(
        self,
        *,
        email: str,
        password: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[Admin, str, str]:
        """Возвращает (admin, access_token, raw_refresh_token).

        raw_refresh_token кладётся роутером в httpOnly-cookie.
        """
        admin = await self._admins.get_by_email(email)

        # Защита от timing attack: verify выполняется всегда.
        password_ok = verify_password(
            password,
            admin.password_hash if admin else _DUMMY_BCRYPT_HASH,
        )

        if admin is None or not password_ok:
            logger.warning("login_failed", email=email, ip_address=ip_address)
            raise InvalidCredentialsError()

        if not admin.is_active:
            logger.warning("login_inactive_admin", admin_id=admin.id)
            raise AdminInactiveError(admin.id)

        await self._admins.update_last_login(admin)

        access = create_access_token(admin.id, admin.role, self._settings)
        raw_refresh, _ = await self._issue_refresh_token(admin.id, user_agent, ip_address)

        await self._session.commit()
        logger.info("login_success", admin_id=admin.id, ip_address=ip_address)
        return admin, access, raw_refresh

    async def refresh(
        self,
        *,
        raw_refresh_token: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[Admin, str, str]:
        """Ротация: отзываем старый refresh, выдаём новый + новый access."""
        token = await self._tokens.get_by_hash(hash_refresh_token(raw_refresh_token))
        if token is None:
            raise TokenInvalidError()
        if token.revoked_at is not None:
            raise RefreshTokenRevokedError()
        if token.expires_at <= datetime.now(UTC):
            raise TokenExpiredError()

        admin = await self._admins.get_by_id(token.admin_id)
        if admin is None:
            raise TokenInvalidError()
        if not admin.is_active:
            raise AdminInactiveError(admin.id)

        await self._tokens.revoke(token)
        access = create_access_token(admin.id, admin.role, self._settings)
        new_raw_refresh, _ = await self._issue_refresh_token(admin.id, user_agent, ip_address)

        await self._session.commit()
        logger.info("token_refreshed", admin_id=admin.id)
        return admin, access, new_raw_refresh

    async def logout(self, *, raw_refresh_token: str) -> None:
        """Отзывает refresh-токен. Не кидает ошибок, если токена нет —
        logout должен быть идемпотентным."""
        token = await self._tokens.get_by_hash(hash_refresh_token(raw_refresh_token))
        if token is not None and token.revoked_at is None:
            await self._tokens.revoke(token)
            await self._session.commit()
            logger.info("logout_success", admin_id=token.admin_id)

    async def authenticate(self, access_token: str) -> Admin:
        """Валидация access-токена, возврат админа. Используется в dependencies."""
        payload = decode_access_token(access_token, self._settings)
        admin = await self._admins.get_by_id(payload.admin_id)
        if admin is None:
            raise TokenInvalidError()
        if not admin.is_active:
            raise AdminInactiveError(admin.id)
        return admin

    async def _issue_refresh_token(
        self,
        admin_id: UUID,
        user_agent: str | None,
        ip_address: str | None,
    ) -> tuple[str, str]:
        raw, token_hash = create_refresh_token()
        await self._tokens.create(
            admin_id=admin_id,
            token_hash=token_hash,
            expires_at=refresh_token_expires_at(self._settings),
            user_agent=user_agent,
            ip_address=ip_address,
        )
        return raw, token_hash


class AdminService:
    def __init__(
        self,
        session: AsyncSession,
        admins: AdminRepository,
        tokens: RefreshTokenRepository,
    ) -> None:
        self._session = session
        self._admins = admins
        self._tokens = tokens

    async def get(self, admin_id: UUID) -> Admin:
        admin = await self._admins.get_by_id(admin_id)
        if admin is None:
            raise AdminNotFoundError(admin_id)
        return admin

    async def list(self, *, limit: int, offset: int) -> tuple[list[Admin], int]:
        items = await self._admins.list(limit=limit, offset=offset)
        total = await self._admins.count()
        return items, total

    async def create(
        self,
        *,
        email: str,
        password: str,
        role: AdminRole,
        full_name: str | None = None,
    ) -> Admin:
        existing = await self._admins.get_by_email(email)
        if existing is not None:
            raise AdminEmailAlreadyExistsError(email)

        admin = await self._admins.create(
            email=email,
            password_hash=hash_password(password),
            role=role,
            full_name=full_name,
        )
        await self._session.commit()
        logger.info("admin_created", admin_id=admin.id, email=email, role=role.value)
        return admin

    async def update(self, admin_id: UUID, fields: dict[str, Any]) -> Admin:
        admin = await self.get(admin_id)

        # Защита "нельзя ронять последнего superadmin".
        role_changing_from_super = (
            admin.role == AdminRole.SUPERADMIN
            and "role" in fields
            and fields["role"] != AdminRole.SUPERADMIN
        )
        deactivating_super = (
            admin.role == AdminRole.SUPERADMIN
            and fields.get("is_active") is False
        )
        if role_changing_from_super or deactivating_super:
            await self._ensure_not_last_superadmin(admin.id)

        # Смена email — проверить уникальность.
        if "email" in fields and fields["email"] != admin.email:
            existing = await self._admins.get_by_email(fields["email"])
            if existing is not None:
                raise AdminEmailAlreadyExistsError(fields["email"])

        await self._admins.update(admin, fields)

        # Если разжаловали/деактивировали — отозвать все токены.
        if role_changing_from_super or fields.get("is_active") is False:
            await self._tokens.revoke_all_for_admin(admin.id)

        await self._session.commit()
        logger.info("admin_updated", admin_id=admin.id, fields=list(fields.keys()))
        return admin

    async def update_self(self, admin_id: UUID, fields: dict[str, Any]) -> Admin:
        """Обновление своих собственных данных.

        В отличие от update() — не требует superadmin прав и не позволяет
        менять role/is_active/email. Проверка полей — на уровне схемы MeUpdate.
        """
        admin = await self.get(admin_id)
        await self._admins.update(admin, fields)
        await self._session.commit()
        logger.info("admin_self_updated", admin_id=admin.id, fields=list(fields.keys()))
        return admin

    async def delete(self, admin_id: UUID) -> None:
        admin = await self.get(admin_id)
        if admin.role == AdminRole.SUPERADMIN:
            await self._ensure_not_last_superadmin(admin.id)

        await self._admins.soft_delete(admin)
        await self._tokens.revoke_all_for_admin(admin.id)
        await self._session.commit()
        logger.info("admin_deleted", admin_id=admin.id)

    async def change_password(
        self,
        *,
        admin_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        admin = await self.get(admin_id)
        if not verify_password(current_password, admin.password_hash):
            raise InvalidCredentialsError()

        await self._admins.update(admin, {"password_hash": hash_password(new_password)})
        # После смены пароля — все сессии слетают.
        await self._tokens.revoke_all_for_admin(admin.id)
        await self._session.commit()
        logger.info("password_changed", admin_id=admin.id)

    async def _ensure_not_last_superadmin(self, admin_id: UUID) -> None:
        """Проверяет, что админ — не единственный активный superadmin.
        """
        stmt = (
            select(func.count())
            .select_from(Admin)
            .where(
                Admin.deleted_at.is_(None),
                Admin.is_active.is_(True),
                Admin.role == AdminRole.SUPERADMIN,
                Admin.id != admin_id,
            )
        )
        others = await self._session.scalar(stmt) or 0
        if others == 0:
            raise ConflictError(
                message="Cannot modify the last active superadmin",
                details={"admin_id": str(admin_id)},
            )