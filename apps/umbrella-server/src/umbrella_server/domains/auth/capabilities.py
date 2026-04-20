"""Capability → roles mapping.

Capability — именованное разрешение вида "resource:action".
Роль админа "содержит" набор capabilities через эту таблицу.
"""

from umbrella_server.domains.auth.models import AdminRole


CAPABILITY_ROLES: dict[str, frozenset[AdminRole]] = {
    # self — любой залогиненный админ
    "self:read": frozenset({AdminRole.VIEWER, AdminRole.ADMIN, AdminRole.SUPERADMIN}),
    "self:update": frozenset({AdminRole.VIEWER, AdminRole.ADMIN, AdminRole.SUPERADMIN}),

    # admins — только superadmin
    "admins:read": frozenset({AdminRole.SUPERADMIN}),
    "admins:write": frozenset({AdminRole.SUPERADMIN}),
}


def roles_for(capability: str) -> frozenset[AdminRole]:
    if capability not in CAPABILITY_ROLES:
        raise RuntimeError(f"Unknown capability: {capability!r}")
    return CAPABILITY_ROLES[capability]