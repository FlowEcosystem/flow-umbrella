"""FastAPI-зависимости auth-домена: current_admin, require_role.

Использование в роутерах:
    from typing import Annotated
    from fastapi import Depends

    async def handler(admin: Annotated[Admin, Depends(current_admin)]): ...

Зависимости совместимы с Dishka через @inject.
"""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from umbrella_server.domains.auth.exceptions import (
    InsufficientPermissionsError,
    TokenInvalidError,
)
from umbrella_server.domains.auth.models import Admin, AdminRole
from umbrella_server.domains.auth.service import AuthService


# auto_error=False — сами кидаем TokenInvalidError вместо дефолтного 403 (принцип единой консистентности исключений)
_bearer_scheme = HTTPBearer(auto_error=False)


@inject
async def current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    auth_service: FromDishka[AuthService],
) -> Admin:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise TokenInvalidError()
    return await auth_service.authenticate(credentials.credentials)


def require_role(
    *allowed_roles: AdminRole,
) -> Callable[[Admin], Coroutine[Any, Any, Admin]]:
    """Фабрика зависимости, проверяющей роль текущего админа.
    """
    allowed = frozenset(allowed_roles)

    async def _check(
        admin: Annotated[Admin, Depends(current_admin)],
    ) -> Admin:
        if admin.role not in allowed:
            raise InsufficientPermissionsError(
                required_role=" | ".join(r.value for r in allowed_roles),
            )
        return admin

    return _check


# Готовые зависимости под типовые случаи.
current_superadmin = require_role(AdminRole.SUPERADMIN)
current_admin_or_above = require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN)
current_any_admin = require_role(AdminRole.SUPERADMIN, AdminRole.ADMIN, AdminRole.VIEWER)


async def current_refresh_token_raw(request: Request) -> str:
    """Достаёт refresh-токен из httpOnly-cookie.

    Имя cookie — 'refresh_token', задаётся роутером при login.
    """
    token = request.cookies.get("refresh_token")
    if not token:
        raise TokenInvalidError()
    return token


def get_client_meta(request: Request) -> tuple[str | None, str | None]:
    """(user_agent, ip_address). IP берётся с учётом nginx-заголовков
    через uvicorn --proxy-headers."""
    ua = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return ua, ip