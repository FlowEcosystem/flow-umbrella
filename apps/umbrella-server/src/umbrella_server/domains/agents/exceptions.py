"""Исключения agents-домена."""

from uuid import UUID

from umbrella_server.core.exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
)


class AgentNotFoundError(NotFoundError):
    error_code = "agent_not_found"

    def __init__(self, agent_id: UUID) -> None:
        super().__init__(
            message=f"Agent {agent_id} not found",
            details={"agent_id": str(agent_id)},
        )


class AgentHostnameAlreadyExistsError(AlreadyExistsError):
    error_code = "agent_hostname_already_exists"

    def __init__(self, hostname: str) -> None:
        super().__init__(
            message=f"Agent with hostname {hostname!r} already exists",
            details={"hostname": hostname},
        )


class AgentDecommissionedError(ConflictError):
    """Операция невозможна над выведенным из эксплуатации агентом."""

    error_code = "agent_decommissioned"

    def __init__(self, agent_id: UUID) -> None:
        super().__init__(
            message=f"Agent {agent_id} is decommissioned",
            details={"agent_id": str(agent_id)},
        )


class AgentAlreadyEnrolledError(ConflictError):
    """Агент уже прошёл enrollment — повторная регенерация токена бессмысленна."""

    error_code = "agent_already_enrolled"

    def __init__(self, agent_id: UUID) -> None:
        super().__init__(
            message=f"Agent {agent_id} is already enrolled",
            details={"agent_id": str(agent_id)},
        )


class EnrollmentTokenInvalidError(AuthenticationError):
    error_code = "enrollment_token_invalid"

    def __init__(self) -> None:
        super().__init__(message="Enrollment token is invalid or has already been used")


class EnrollmentTokenExpiredError(AuthenticationError):
    error_code = "enrollment_token_expired"

    def __init__(self) -> None:
        super().__init__(message="Enrollment token has expired")


class AgentTokenInvalidError(AuthenticationError):
    error_code = "agent_token_invalid"

    def __init__(self) -> None:
        super().__init__(message="Agent token is invalid")