"""Исключения groups-домена."""

from uuid import UUID

from umbrella_server.core.exceptions import (
    AlreadyExistsError,
    ConflictError,
    NotFoundError,
)


class GroupNotFoundError(NotFoundError):
    error_code = "group_not_found"

    def __init__(self, group_id: UUID) -> None:
        super().__init__(
            message=f"Group {group_id} not found",
            details={"group_id": str(group_id)},
        )


class GroupNameAlreadyExistsError(AlreadyExistsError):
    error_code = "group_name_already_exists"

    def __init__(self, name: str) -> None:
        super().__init__(
            message=f"Group with name {name!r} already exists",
            details={"name": name},
        )


class AgentsNotFoundError(ConflictError):
    """Часть агентов из batch-add не найдены в БД."""

    error_code = "agents_not_found"

    def __init__(self, missing_ids: list[UUID]) -> None:
        super().__init__(
            message=f"{len(missing_ids)} agent(s) not found",
            details={"missing_agent_ids": [str(i) for i in missing_ids]},
        )