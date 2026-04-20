"""HTTP-роутеры auth-домена: /api/admins/*."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, status

from umbrella_server.core.exceptions import ConflictError
from umbrella_server.core.pagination import Page, PaginationMeta, PaginationParams
from umbrella_server.domains.auth.dependencies import (
    current_superadmin,
)
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.auth.schemas import (
    AdminCreate,
    AdminRead,
    AdminUpdate,
)
from umbrella_server.domains.auth.service import AdminService


admins_router = APIRouter(prefix="/v1/admins", tags=["admins"])

@admins_router.post("", response_model=AdminRead, status_code=status.HTTP_201_CREATED)
@inject
async def create_admin(
    payload: AdminCreate,
    _current: Annotated[Admin, Depends(current_superadmin)],
    admin_service: FromDishka[AdminService],
) -> AdminRead:
    admin = await admin_service.create(
        email=payload.email,
        password=payload.password,
        role=payload.role,
        full_name=payload.full_name,
    )
    return AdminRead.model_validate(admin)


@admins_router.get("", response_model=Page[AdminRead])
@inject
async def list_admins(
    _current: Annotated[Admin, Depends(current_superadmin)],
    pagination: Annotated[PaginationParams, Depends()],
    admin_service: FromDishka[AdminService],
) -> Page[AdminRead]:
    items, total = await admin_service.list(
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return Page[AdminRead](
        items=[AdminRead.model_validate(a) for a in items],
        meta=PaginationMeta(total=total, limit=pagination.limit, offset=pagination.offset),
    )


@admins_router.get("/{admin_id}", response_model=AdminRead)
@inject
async def get_admin(
    admin_id: UUID,
    _current: Annotated[Admin, Depends(current_superadmin)],
    admin_service: FromDishka[AdminService],
) -> AdminRead:
    admin = await admin_service.get(admin_id)
    return AdminRead.model_validate(admin)


@admins_router.patch("/{admin_id}", response_model=AdminRead)
@inject
async def update_admin(
    admin_id: UUID,
    payload: AdminUpdate,
    current: Annotated[Admin, Depends(current_superadmin)],
    admin_service: FromDishka[AdminService],
) -> AdminRead:
    if admin_id == current.id:
        raise ConflictError(
            message="Use /v1/auth/me/password to change your own credentials",
            details={"admin_id": str(admin_id)},
        )
    fields = payload.model_dump(exclude_unset=True)
    admin = await admin_service.update(admin_id, fields)
    return AdminRead.model_validate(admin)


@admins_router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_admin(
    admin_id: UUID,
    current: Annotated[Admin, Depends(current_superadmin)],
    admin_service: FromDishka[AdminService],
) -> None:
    if admin_id == current.id:
        raise ConflictError(
            message="You cannot delete yourself",
            details={"admin_id": str(admin_id)},
        )
    await admin_service.delete(admin_id)