"""Branch CA — генерация, загрузка и подпись сертификатов агентов."""

import datetime
from pathlib import Path
from uuid import UUID

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from umbrella_server.core.logging import get_logger

logger = get_logger(__name__)

# TTL клиентского сертификата агента.
_AGENT_CERT_TTL_DAYS = 30

# TTL серверного TLS-сертификата (nginx).
_SERVER_CERT_TTL_DAYS = 365

# RSA key size для CA и агентских сертификатов.
_KEY_BITS = 2048


class BranchCA:
    """Локальный CA филиала.

    Загружается один раз при старте приложения и живёт в DI-контейнере
    с APP-scope. Используется только для подписи CSR при enrollment агентов.
    """

    def __init__(self, cert: x509.Certificate, key: rsa.RSAPrivateKey) -> None:
        self._cert = cert
        self._key = key

    # ------------------------------------------------------------------
    # Фабричные методы
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, cert_path: Path, key_path: Path) -> "BranchCA":
        """Загружает существующий CA из PEM-файлов."""
        cert_pem = cert_path.read_bytes()
        key_pem = key_path.read_bytes()
        cert = x509.load_pem_x509_certificate(cert_pem)
        key = serialization.load_pem_private_key(key_pem, password=None)
        logger.info("pki_ca_loaded", subject=cert.subject.rfc4514_string())
        return cls(cert, key)  # type: ignore[arg-type]

    @classmethod
    def generate(cls, branch_name: str, cert_path: Path, key_path: Path) -> "BranchCA":
        """Генерирует новый root CA и сохраняет в PEM-файлы.

        Вызывается автоматически из ensure_ca() если файлов ещё нет.
        """
        key = rsa.generate_private_key(public_exponent=65537, key_size=_KEY_BITS)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, f"Umbrella Branch CA — {branch_name}"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Umbrella"),
        ])
        now = datetime.datetime.now(datetime.UTC)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=3650))  # 10 лет
            .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True, key_cert_sign=True, crl_sign=True,
                    content_commitment=False, key_encipherment=False,
                    data_encipherment=False, key_agreement=False,
                    encipher_only=False, decipher_only=False,
                ),
                critical=True,
            )
            .sign(key, hashes.SHA256())
        )

        cert_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.parent.mkdir(parents=True, exist_ok=True)

        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        key_path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )
        key_path.chmod(0o600)

        logger.info("pki_ca_generated", cert_path=str(cert_path), key_path=str(key_path))
        return cls(cert, key)

    @classmethod
    def ensure(cls, cert_path: Path, key_path: Path, branch_name: str) -> "BranchCA":
        """Загружает CA если файлы есть, генерирует если нет."""
        if cert_path.exists() and key_path.exists():
            return cls.load(cert_path, key_path)
        return cls.generate(branch_name, cert_path, key_path)

    # ------------------------------------------------------------------
    # Подпись CSR
    # ------------------------------------------------------------------

    def sign_csr(
        self, csr_pem: bytes, agent_id: UUID
    ) -> tuple[bytes, int, datetime.datetime]:
        """Подписывает CSR агента.

        Возвращает (cert_pem, serial_number, not_valid_after).
        CN сертификата = agent:<agent_id>, чтобы можно было идентифицировать
        агента по сертификату при будущем переходе на mTLS.
        """
        csr = x509.load_pem_x509_csr(csr_pem)
        now = datetime.datetime.now(datetime.UTC)
        serial = x509.random_serial_number()

        cert = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, f"agent:{agent_id}"),
            ]))
            .issuer_name(self._cert.subject)
            .public_key(csr.public_key())
            .serial_number(serial)
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=_AGENT_CERT_TTL_DAYS))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True, key_encipherment=True,
                    content_commitment=False, data_encipherment=False,
                    key_agreement=False, key_cert_sign=False, crl_sign=False,
                    encipher_only=False, decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
                critical=False,
            )
            .sign(self._key, hashes.SHA256())
        )

        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        not_after = cert.not_valid_after_utc
        logger.info(
            "agent_cert_signed",
            agent_id=str(agent_id),
            serial=serial,
            expires=not_after.isoformat(),
        )
        return cert_pem, serial, not_after

    def sign_server_cert(
        self,
        hostname: str,
        cert_path: Path,
        key_path: Path,
    ) -> None:
        """Генерирует TLS-сертификат для nginx, подписанный этим CA.

        Агент верифицирует сервер через ca_cert_pem из enrollment —
        этот сертификат пройдёт проверку автоматически.
        SAN обязателен: Go 1.15+ проверяет именно его, а не только CN.
        """
        key = rsa.generate_private_key(public_exponent=65537, key_size=_KEY_BITS)
        now = datetime.datetime.now(datetime.UTC)

        cert = (
            x509.CertificateBuilder()
            .subject_name(x509.Name([
                x509.NameAttribute(NameOID.COMMON_NAME, hostname),
            ]))
            .issuer_name(self._cert.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=_SERVER_CERT_TTL_DAYS))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True, key_encipherment=True,
                    content_commitment=False, data_encipherment=False,
                    key_agreement=False, key_cert_sign=False, crl_sign=False,
                    encipher_only=False, decipher_only=False,
                ),
                critical=True,
            )
            .add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
                critical=False,
            )
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(hostname)]),
                critical=False,
            )
            .sign(self._key, hashes.SHA256())
        )

        cert_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.parent.mkdir(parents=True, exist_ok=True)

        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        key_path.write_bytes(
            key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption(),
            )
        )
        key_path.chmod(0o600)

        logger.info(
            "server_cert_generated",
            hostname=hostname,
            cert_path=str(cert_path),
            expires=cert.not_valid_after_utc.isoformat(),
        )

    def ca_cert_pem(self) -> bytes:
        return self._cert.public_bytes(serialization.Encoding.PEM)

    @property
    def cert_expires_at(self) -> datetime.datetime:
        return self._cert.not_valid_after_utc
