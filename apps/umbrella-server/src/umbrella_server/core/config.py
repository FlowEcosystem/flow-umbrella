from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    dev = "dev"
    test = "test"
    prod = "prod"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- core ---
    env: AppEnv = AppEnv.dev
    debug: bool = False
    secret_key: SecretStr
    cors_origins: str = ""

    # --- db ---
    database_url: PostgresDsn
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # --- PKI ---
    pki_ca_cert_path: Path | None = None
    pki_ca_key_path: Path | None = None
    # ECDSA P-256 ключ для offline-токенов деинсталляции. Генерируется автоматически
    # при первом запуске, если файл не существует.
    decommission_key_path: Path | None = None

    # --- agent intervals ---
    policy_poll_interval_sec: int = 60
    command_poll_interval_sec: int = 15
    metrics_push_interval_sec: int = 60
    # Сколько секунд без heartbeat → статус агента переходит в disabled.
    # По умолчанию 45 с = 3× heartbeat-интервал (15 с).
    agent_offline_timeout_sec: int = 45

    # --- auth ---
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_min: int = 60
    jwt_refresh_ttl_days: int = 14

    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None

    # --- agents ---
    agent_enrollment_token_ttl_days: int = 7
    # true  — prod: агент аутентифицируется через X-Agent-Cert-CN от nginx (mTLS)
    # false — dev: fallback на bearer token без nginx
    agent_mtls: bool = True

    @field_validator("database_url")
    @classmethod
    def _ensure_asyncpg(cls, v: PostgresDsn) -> PostgresDsn:
        if "+asyncpg" not in str(v):
            raise ValueError("database_url must use postgresql+asyncpg:// scheme")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @model_validator(mode="after")
    def _validate_cookie_policy(self) -> "Settings":
        if self.cookie_samesite == "none" and not self.cookie_secure:
            raise ValueError(
                "cookie_samesite='none' requires cookie_secure=true "
                "(browsers reject insecure cross-site cookies)"
            )
        return self

    @property
    def database_url_sync(self) -> str:
        return str(self.database_url).replace("postgresql+asyncpg://", "postgresql://")

    @property
    def is_prod(self) -> bool:
        return self.env is AppEnv.prod


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]