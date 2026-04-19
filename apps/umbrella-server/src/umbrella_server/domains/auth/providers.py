"""Dishka-провайдер auth-домена."""

from dishka import Provider, Scope, provide

from umbrella_server.domains.auth.repository import (
    AdminRepository,
    RefreshTokenRepository,
)
from umbrella_server.domains.auth.service import AdminService, AuthService


class AuthProvider(Provider):
    scope = Scope.REQUEST

    admin_repo = provide(AdminRepository)
    refresh_token_repo = provide(RefreshTokenRepository)
    auth_service = provide(AuthService)
    admin_service = provide(AdminService)