"""Исключения auth-домена."""

from uuid import UUID

from umbrella_server.core.exceptions import (
    AlreadyExistsError,
    DomainError,
    NotFoundError,
)


class InvalidCredentialsError(DomainError):
    error_code = "invalid_credentials"

    def __init__(self) -> None:
        super().__init__(message="Invalid email or password")


class AdminInactiveError(DomainError):
    error_code = "admin_inactive"

    def __init__(self, admin_id: UUID) -> None:
        super().__init__(
            message="Admin account is inactive",
            details={"admin_id": str(admin_id)},
        )


class AdminNotFoundError(NotFoundError):
    error_code = "admin_not_found"

    def __init__(self, admin_id: UUID) -> None:
        super().__init__(
            message=f"Admin {admin_id} not found",
            details={"admin_id": str(admin_id)},
        )


class AdminEmailAlreadyExistsError(AlreadyExistsError):
    error_code = "admin_email_already_exists"

    def __init__(self, email: str) -> None:
        super().__init__(
            message=f"Admin with email {email!r} already exists",
            details={"email": email},
        )


class TokenInvalidError(DomainError):
    error_code = "token_invalid"

    def __init__(self) -> None:
        super().__init__(message="Token is invalid or malformed")


class TokenExpiredError(DomainError):
    error_code = "token_expired"

    def __init__(self) -> None:
        super().__init__(message="Token has expired")


class RefreshTokenRevokedError(DomainError):
    error_code = "refresh_token_revoked"

    def __init__(self) -> None:
        super().__init__(message="Refresh token has been revoked")


class InsufficientPermissionsError(DomainError):
    error_code = "insufficient_permissions"

    def __init__(self, required_role: str) -> None:
        super().__init__(
            message=f"Requires role: {required_role}",
            details={"required_role": required_role},
        )