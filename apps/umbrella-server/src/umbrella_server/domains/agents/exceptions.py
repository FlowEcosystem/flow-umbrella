"""Исключения agents-домена."""

from uuid import UUID

from umbrella_server.core.exceptions import (
    AlreadyExistsError,
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