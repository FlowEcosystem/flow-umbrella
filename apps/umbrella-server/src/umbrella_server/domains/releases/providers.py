"""Dishka-провайдер домена releases."""

from dishka import Provider, Scope, provide

from umbrella_server.domains.releases.service import ReleasesService


class ReleasesProvider(Provider):
    scope = Scope.REQUEST

    releases_service = provide(ReleasesService)
