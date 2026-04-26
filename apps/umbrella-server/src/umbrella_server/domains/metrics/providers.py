"""Dishka-провайдер домена метрик."""

from dishka import Provider, Scope, provide

from umbrella_server.domains.metrics.repository import MetricsRepository
from umbrella_server.domains.metrics.service import MetricsService


class MetricsProvider(Provider):
    scope = Scope.REQUEST

    metrics_repo = provide(MetricsRepository)
    metrics_service = provide(MetricsService)
