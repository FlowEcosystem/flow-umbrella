"""Агрегатор всех моделей для Alembic autogenerate."""

from umbrella_server.db.base import Base
from umbrella_server.domains.auth.models import Admin, RefreshToken 
from umbrella_server.domains.instance.models import BranchConfig  # noqa: F401

__all__ = ["Base", "Admin", "RefreshToken", "BranchConfig"]