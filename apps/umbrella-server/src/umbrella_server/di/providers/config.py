"""Провайдер настроек приложения."""

from dishka import Provider, Scope, provide

from umbrella_server.core.config import Settings, get_settings


class ConfigProvider(Provider):
    """Отдаёт Settings из get_settings() (lru_cache внутри)."""

    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        return get_settings()