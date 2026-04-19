"""Общие схемы пагинации."""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query-параметры для list-endpoints. Используется через Depends."""
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class PaginationMeta(BaseModel):
    total: int
    limit: int
    offset: int


class Page(BaseModel, Generic[T]):
    """Generic-ответ на list-endpoint.

    Использование:
        class AdminListResponse(Page[AdminRead]): pass
        # или напрямую:
        response_model=Page[AdminRead]
    """
    items: list[T]
    meta: PaginationMeta