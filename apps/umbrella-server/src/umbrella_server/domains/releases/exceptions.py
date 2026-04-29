"""Исключения домена releases."""

from umbrella_server.core.exceptions import NotFoundError


class AgentReleaseNotFoundError(NotFoundError):
    error_code = "agent_release_not_found"

    def __init__(self, release_id: str) -> None:
        super().__init__(
            message=f"Agent release {release_id} not found",
            details={"release_id": release_id},
        )
