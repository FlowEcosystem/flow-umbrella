"""Точка входа FastAPI-приложения."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from umbrella_server.core.config import get_settings
from umbrella_server.core.logging import configure_logging, get_logger
from umbrella_server.di import build_container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup и shutdown логика.
    """
    logger = get_logger(__name__)
    settings = get_settings()
    logger.info("app_started", env=settings.env.value, debug=settings.debug)

    yield

    logger.info("app_shutting_down")
    await app.state.dishka_container.close()
    logger.info("app_stopped")


def create_app() -> FastAPI:
    """Application factory. Вызывается uvicorn'ом."""
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="Umbrella Server",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_prod else None,
        redoc_url=None,
    )

    container = build_container()
    setup_dishka(container=container, app=app)

    # routes

    return app


app = create_app()