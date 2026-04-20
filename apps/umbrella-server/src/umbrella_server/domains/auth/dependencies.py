"""FastAPI-зависимости auth-домена."""

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from umbrella_server.domains.auth.capabilities import roles_for
from umbrella_server.domains.auth.exceptions import (
    InsufficientPermissionsError,
    TokenInvalidError,
)
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.auth.service import AuthService


_bearer_scheme = HTTPBearer(auto_error=False)


@inject
async def current_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    auth_service: FromDishka[AuthService],
) -> Admin:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise TokenInvalidError()
    return await auth_service.authenticate(credentials.credentials)


def require_capability(
    capability: str,
) -> Callable[[Admin], Coroutine[Any, Any, Admin]]:
    # Резолвим роли один раз при регистрации зависимости, не на каждый запрос.
    allowed = roles_for(capability)

    async def _check(
        admin: Annotated[Admin, Depends(current_admin)],
    ) -> Admin:
        if admin.role not in allowed:
            raise InsufficientPermissionsError(required_role=capability)
        return admin

    return _check


# Шорткаты для читаемости в роутерах.
current_any_admin = require_capability("self:read")
current_superadmin = require_capability("admins:write")


async def current_refresh_token_raw(request: Request) -> str:
    token = request.cookies.get("refresh_token")
    if not token:
        raise TokenInvalidError()
    return token


def get_client_meta(request: Request) -> tuple[str | None, str | None]:
    ua = request.headers.get("user-agent")
    ip = request.client.host if request.client else None
    return ua, ip