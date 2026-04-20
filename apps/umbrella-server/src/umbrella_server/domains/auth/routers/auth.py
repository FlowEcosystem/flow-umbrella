"""HTTP-роутеры auth-домена: /api/auth/* """

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Request, Response, status

from umbrella_server.core.config import Settings
from umbrella_server.domains.auth.dependencies import (
    current_any_admin,
    current_refresh_token_raw,
    get_client_meta,
)
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.auth.schemas import (
    LoginRequest,
    MeResponse,
    PasswordChange,
    TokenResponse,
)
from umbrella_server.domains.auth.service import AdminService, AuthService


auth_router = APIRouter(prefix="/v1/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, raw_refresh: str, settings: Settings) -> None:
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.jwt_refresh_ttl_days * 86400,
        path="/v1/auth",
        domain=settings.cookie_domain or None,
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key="refresh_token",
        path="/v1/auth",
        domain=settings.cookie_domain or None,
    )


@auth_router.post("/login", response_model=TokenResponse)
@inject
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    auth_service: FromDishka[AuthService],
    settings: FromDishka[Settings],
) -> TokenResponse:
    user_agent, ip = get_client_meta(request)
    _, access, raw_refresh = await auth_service.login(
        email=payload.email,
        password=payload.password,
        user_agent=user_agent,
        ip_address=ip,
    )
    _set_refresh_cookie(response, raw_refresh, settings)
    return TokenResponse(
        access_token=access,
        expires_in=settings.jwt_access_ttl_min * 60,
    )


@auth_router.post("/refresh", response_model=TokenResponse)
@inject
async def refresh(
    request: Request,
    response: Response,
    raw_refresh: Annotated[str, Depends(current_refresh_token_raw)],
    auth_service: FromDishka[AuthService],
    settings: FromDishka[Settings],
) -> TokenResponse:
    user_agent, ip = get_client_meta(request)
    _, access, new_raw_refresh = await auth_service.refresh(
        raw_refresh_token=raw_refresh,
        user_agent=user_agent,
        ip_address=ip,
    )
    _set_refresh_cookie(response, new_raw_refresh, settings)
    return TokenResponse(
        access_token=access,
        expires_in=settings.jwt_access_ttl_min * 60,
    )


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def logout(
    request: Request,
    response: Response,
    auth_service: FromDishka[AuthService],
    settings: FromDishka[Settings],
) -> None:
    # logout делаем мягким: если куки нет — просто очищаем, не кидаем.
    raw = request.cookies.get("refresh_token")
    if raw:
        await auth_service.logout(raw_refresh_token=raw)
    _clear_refresh_cookie(response, settings)


@auth_router.get("/me", response_model=MeResponse)
async def me(
    admin: Annotated[Admin, Depends(current_any_admin)],
) -> MeResponse:
    return MeResponse.model_validate(admin)

from umbrella_server.domains.auth.schemas import MeUpdate


@auth_router.patch("/me", response_model=MeResponse)
@inject
async def update_me(
    payload: MeUpdate,
    admin: Annotated[Admin, Depends(current_any_admin)],
    admin_service: FromDishka[AdminService],
) -> MeResponse:
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        # Пустой PATCH — возвращаем как есть, не трогаем БД.
        return MeResponse.model_validate(admin)
    updated = await admin_service.update_self(admin.id, fields)
    return MeResponse.model_validate(updated)

@auth_router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def change_my_password(
    payload: PasswordChange,
    admin: Annotated[Admin, Depends(current_any_admin)],
    response: Response,
    admin_service: FromDishka[AdminService],
    settings: FromDishka[Settings],
) -> None:
    await admin_service.change_password(
        admin_id=admin.id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    # Все refresh отозваны — clearим cookie, чтобы фронт не ходил с мёртвым токеном.
    _clear_refresh_cookie(response, settings)