"""Точка входа FastAPI-приложения."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from umbrella_server.core.config import get_settings
from umbrella_server.core.logging import configure_logging, get_logger
from umbrella_server.di import build_container
from umbrella_server.domains.auth.router import admins_router, auth_router
from umbrella_server.middleware.exception_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = get_logger(__name__)
    settings = get_settings()
    logger.info("app_started", env=settings.env.value, debug=settings.debug)

    yield

    logger.info("app_shutting_down")
    await app.state.dishka_container.close()
    logger.info("app_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="Umbrella Server",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_prod else None,
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    container = build_container()
    setup_dishka(container=container, app=app)

    # /v1/*
    app.include_router(auth_router)
    app.include_router(admins_router)

    return app


app = create_app()