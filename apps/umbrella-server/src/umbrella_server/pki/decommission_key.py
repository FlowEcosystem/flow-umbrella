"""ECDSA P-256 ключ для offline-токенов деинсталляции агентов.

Приватный ключ хранится только на сервере. Агенты получают публичный ключ
при enrollment и используют его для верификации токена без обращения к серверу.
"""

import base64
from datetime import UTC, datetime
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from umbrella_server.core.logging import get_logger

logger = get_logger(__name__)


class DecommissionKey:
    def __init__(self, private_key: ec.EllipticCurvePrivateKey) -> None:
        self._key = private_key

    @classmethod
    def load_or_generate(cls, key_path: Path) -> "DecommissionKey":
        if key_path.exists():
            with open(key_path, "rb") as f:
                key = serialization.load_pem_private_key(f.read(), password=None)
            logger.info("decommission_key_loaded", path=str(key_path))
        else:
            key = ec.generate_private_key(ec.SECP256R1())
            key_path.parent.mkdir(parents=True, exist_ok=True)
            with open(key_path, "wb") as f:
                f.write(key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                ))
            logger.info("decommission_key_generated", path=str(key_path))
        return cls(key)  # type: ignore[arg-type]

    def public_key_pem(self) -> str:
        return self._key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

    def sign(self, agent_id: str) -> tuple[str, datetime]:
        """Подписывает токен для текущего UTC-дня.

        Возвращает (base64url_token, expires_at).
        Агент принимает токены за текущий и предыдущий день (48-часовое окно).
        """
        now = datetime.now(UTC)
        day_stamp = int(now.timestamp() // 86400) * 86400
        msg = f"decommission:{agent_id}:{day_stamp}".encode()
        sig = self._key.sign(msg, ec.ECDSA(hashes.SHA256()))
        token = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
        expires_at = datetime.fromtimestamp(day_stamp + 86400 * 2, tz=UTC)
        return token, expires_at
