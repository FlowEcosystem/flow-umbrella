from dishka import Provider, Scope, provide

from umbrella_server.domains.audit.repository import AuditRepository
from umbrella_server.domains.audit.service import AuditService


class AuditProvider(Provider):
    scope = Scope.REQUEST

    audit_repo = provide(AuditRepository)
    audit_service = provide(AuditService)
