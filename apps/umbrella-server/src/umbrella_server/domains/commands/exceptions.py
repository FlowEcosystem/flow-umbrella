"""Исключения домена команд."""

from uuid import UUID

from umbrella_server.core.exceptions import ConflictError, NotFoundError


class CommandNotFoundError(NotFoundError):
    error_code = "command_not_found"

    def __init__(self, command_id: UUID) -> None:
        super().__init__(
            message=f"Command {command_id} not found",
            details={"command_id": str(command_id)},
        )


class CommandInvalidStatusError(ConflictError):
    error_code = "command_invalid_status"

    def __init__(self, command_id: UUID, current: str, expected: str) -> None:
        super().__init__(
            message=f"Command {command_id} is {current!r}, expected {expected!r}",
            details={"command_id": str(command_id), "current": current, "expected": expected},
        )
