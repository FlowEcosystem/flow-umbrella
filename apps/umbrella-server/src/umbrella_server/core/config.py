from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, PostgresDsn, SecretStr, field_validator
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
    cors_origins: list[str] = Field(default_factory=list)

    # --- db ---
    database_url: PostgresDsn
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # --- PKI ---
    pki_ca_cert_path: Path | None = None
    pki_ca_key_path: Path | None = None

    # --- agent intervals ---
    policy_poll_interval_sec: int = 60
    command_poll_interval_sec: int = 15
    metrics_push_interval_sec: int = 60

    @field_validator("database_url")
    @classmethod
    def _ensure_asyncpg(cls, v: PostgresDsn) -> PostgresDsn:
        if "+asyncpg" not in str(v):
            raise ValueError("database_url must use postgresql+asyncpg:// scheme")
        return v

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @property
    def database_url_sync(self) -> str:
        return str(self.database_url).replace("postgresql+asyncpg://", "postgresql://")

    @property
    def is_prod(self) -> bool:
        return self.env is AppEnv.prod


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]