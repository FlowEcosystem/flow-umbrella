"""Pydantic-схемы auth-домена.

Разделение по use-case:
- LoginRequest / TokenResponse / MeResponse — auth-flow
- AdminCreate / AdminUpdate / AdminRead — CRUD админов
- PasswordChange — смена пароля текущего админа
- AdminListResponse — пагинированный список
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from umbrella_server.domains.auth.models import AdminRole


# -----------------------------------------------------------------------------
# Auth flow
# -----------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    avatar_url: str | None
    role: AdminRole
    is_active: bool
    last_login_at: datetime | None

class MeUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    avatar_url: str | None = Field(default=None, max_length=2048)

# -----------------------------------------------------------------------------
# Admin CRUD
# -----------------------------------------------------------------------------

class AdminCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str | None = Field(default=None, max_length=255)
    role: AdminRole = AdminRole.ADMIN


class AdminUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    role: AdminRole | None = None
    is_active: bool | None = None


class AdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str | None
    avatar_url: str | None
    role: AdminRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)
