"""Исключения instance-домена."""

from umbrella_server.core.exceptions import ConflictError, DomainError


class InstanceNotInitializedError(DomainError):
    error_code = "instance_not_initialized"

    def __init__(self) -> None:
        super().__init__(message="Branch instance is not initialized")


class HqAlreadyEnrolledError(ConflictError):
    error_code = "hq_already_enrolled"

    def __init__(self) -> None:
        super().__init__(message="Branch is already enrolled in HQ")


class HqNotConfiguredError(DomainError):
    error_code = "hq_not_configured"

    def __init__(self) -> None:
        super().__init__(message="HQ connection is not configured")