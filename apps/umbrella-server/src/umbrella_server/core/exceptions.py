"""Базовая иерархия исключений Umbrella.

Правила:
- Сервисы и репозитории кидают эти исключения, а не HTTPException.
- HTTP-маппинг делается в middleware/exception_handlers.py.
- Конкретные доменные исключения живут в domains/<name>/exceptions.py.
"""

from typing import Any


class UmbrellaError(Exception):
    """Корень всей иерархии. Всё приложение должно кидать только это и наследников."""

    # HTTP-статус по умолчанию. Переопределяется в подклассах.
    default_status_code: int = 500

    # Машиночитаемый код ошибки.
    error_code: str = "internal_error"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Сериализация для HTTP-ответа и structlog."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# -----------------------------------------------------------------------------
# Domain errors — 4xx, виноват клиент / бизнес-правила не позволяют
# -----------------------------------------------------------------------------

class DomainError(UmbrellaError):
    """База для всех бизнес-ошибок. Логируются как WARNING, не ERROR."""

    default_status_code = 400
    error_code = "domain_error"


class NotFoundError(DomainError):
    """Запрошенная сущность не существует."""

    default_status_code = 404
    error_code = "not_found"


class AlreadyExistsError(DomainError):
    """Сущность с такими идентификаторами уже есть.
    """

    default_status_code = 409
    error_code = "already_exists"


class ConflictError(DomainError):
    """Состояние сущности не позволяет выполнить операцию.
    """

    default_status_code = 409
    error_code = "conflict"


class ValidationError(DomainError):
    """Бизнес-валидация не прошла.
    """

    default_status_code = 422
    error_code = "validation_error"


class AuthenticationError(DomainError):
    """Клиент не смог доказать, кто он.
    """

    default_status_code = 401
    error_code = "authentication_failed"


class PermissionDeniedError(DomainError):
    """Клиент опознан, но не имеет прав на эту операцию.
    """

    default_status_code = 403
    error_code = "permission_denied"


# -----------------------------------------------------------------------------
# Infrastructure errors — 5xx, виноват сервер / инфра
# -----------------------------------------------------------------------------

class InfrastructureError(UmbrellaError):
    """База для проблем с инфраструктурой. Логируются как ERROR, идут в Sentry."""

    default_status_code = 500
    error_code = "infrastructure_error"


class DatabaseError(InfrastructureError):
    """Что-то сломалось на уровне БД.
    """

    error_code = "database_error"


class ExternalServiceError(InfrastructureError):
    """Внешний сервис (почта, SIEM, webhook) недоступен или ответил ошибкой.
    """

    default_status_code = 502
    error_code = "external_service_error"


class ConfigurationError(InfrastructureError):
    """Конфиг приложения невалиден в рантайме.
    """

    error_code = "configuration_error"