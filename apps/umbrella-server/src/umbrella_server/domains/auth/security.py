"""Хэширование паролей и работа с JWT/refresh-токенами.
"""

import hashlib
import secrets
import bcrypt
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from umbrella_server.core.config import Settings
from umbrella_server.domains.auth.exceptions import (
    TokenExpiredError,
    TokenInvalidError,
)
from umbrella_server.domains.auth.models import AdminRole


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


# -----------------------------------------------------------------------------
# JWT access token
# -----------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class AccessTokenPayload:
    admin_id: UUID
    role: AdminRole
    jti: UUID
    issued_at: datetime
    expires_at: datetime


def create_access_token(
    admin_id: UUID,
    role: AdminRole,
    settings: Settings,
) -> str:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=settings.jwt_access_ttl_min)
    payload = {
        "sub": str(admin_id),
        "role": role.value,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": str(uuid4()),
    }
    return jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str, settings: Settings) -> AccessTokenPayload:
    """Валидирует подпись и срок, возвращает распарсенный payload.

    Raises:
        TokenExpiredError: токен истёк.
        TokenInvalidError: невалидная подпись, неверный тип, битая структура.
    """
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as e:
        raise TokenExpiredError() from e
    except JWTError as e:
        raise TokenInvalidError() from e

    if payload.get("type") != "access":
        raise TokenInvalidError()

    try:
        return AccessTokenPayload(
            admin_id=UUID(payload["sub"]),
            role=AdminRole(payload["role"]),
            jti=UUID(payload["jti"]),
            issued_at=datetime.fromtimestamp(payload["iat"], tz=UTC),
            expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
        )
    except (KeyError, ValueError) as e:
        raise TokenInvalidError() from e


# -----------------------------------------------------------------------------
# Refresh token (случайная строка + SHA-256 в БД)
# -----------------------------------------------------------------------------

# 32 байта = 256 бит энтропии. urlsafe-base64 даёт ~43 символа без =.
_REFRESH_TOKEN_BYTES = 32


def create_refresh_token() -> tuple[str, str]:
    """Генерит refresh-токен. Возвращает (raw, hash).

    raw отдаётся клиенту в cookie.
    hash сохраняется в БД — по нему ищем при проверке.
    Сам raw в БД НЕ хранится.
    """
    raw = secrets.token_urlsafe(_REFRESH_TOKEN_BYTES)
    return raw, hash_refresh_token(raw)


def hash_refresh_token(raw: str) -> str:
    """SHA-256 в hex. Используется и при создании, и при проверке."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def refresh_token_expires_at(settings: Settings) -> datetime:
    return datetime.now(UTC) + timedelta(days=settings.jwt_refresh_ttl_days)