"""Исключения policies-домена."""

from uuid import UUID

from umbrella_server.core.exceptions import AlreadyExistsError, NotFoundError, PermissionDeniedError


class PolicyNotFoundError(NotFoundError):
    error_code = "policy_not_found"

    def __init__(self, policy_id: UUID) -> None:
        super().__init__(
            message=f"Policy {policy_id} not found",
            details={"policy_id": str(policy_id)},
        )


class PolicyNameAlreadyExistsError(AlreadyExistsError):
    error_code = "policy_name_already_exists"

    def __init__(self, name: str) -> None:
        super().__init__(
            message=f"Policy with name {name!r} already exists",
            details={"name": name},
        )


class PolicyReadOnlyError(PermissionDeniedError):
    error_code = "policy_read_only"

    def __init__(self, policy_id: UUID) -> None:
        super().__init__(
            message=f"Policy {policy_id} is global and cannot be modified on a branch",
            details={"policy_id": str(policy_id)},
        )


class ServiceNotFoundError(NotFoundError):
    error_code = "service_not_found"

    def __init__(self, service_id: UUID) -> None:
        super().__init__(
            message=f"Service {service_id} not found",
            details={"service_id": str(service_id)},
        )


class ServiceNameAlreadyExistsError(AlreadyExistsError):
    error_code = "service_name_already_exists"

    def __init__(self, name: str) -> None:
        super().__init__(
            message=f"Service with name {name!r} already exists",
            details={"name": name},
        )


class ServiceReadOnlyError(PermissionDeniedError):
    error_code = "service_read_only"

    def __init__(self, service_id: UUID) -> None:
        super().__init__(
            message=f"Service {service_id} is global and cannot be modified on a branch",
            details={"service_id": str(service_id)},
        )
