from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = Path(__file__).parent
_ENV_FILE = _HERE.parent.parent.parent / ".env"  # apps/umbrella-server/.env

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SERVER_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- core ---
    debug: bool = False
    secret_key: SecretStr
    cors_origins: list[str] = Field(default_factory=list)

    # --- db ---
    database_url: PostgresDsn
    database_echo: bool = False
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # --- PKI ---
    pki_ca_cert_path: Path = Path("/etc/umbrella/pki/ca.crt")
    pki_ca_key_path: Path = Path("/etc/umbrella/pki/ca.key")

    # --- intervals (для агентов) ---
    policy_poll_interval_sec: int = 60
    command_poll_interval_sec: int = 15
    metrics_push_interval_sec: int = 60

    @property
    def database_url_sync(self) -> str:
        return str(self.database_url).replace("postgresql+asyncpg://", "postgresql://")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]