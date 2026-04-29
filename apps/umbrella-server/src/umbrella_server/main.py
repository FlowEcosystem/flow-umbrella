"""Точка входа FastAPI-приложения."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from umbrella_server.core.config import Settings, get_settings
from umbrella_server.core.logging import configure_logging, get_logger
from umbrella_server.di import build_container
from umbrella_server.middleware.exception_handlers import register_exception_handlers
from umbrella_server.domains.instance.bootstrap import ensure_instance
from umbrella_server.domains.agents.repository import AgentRepository
from umbrella_server.pki import BranchCA

from umbrella_server.domains.auth.routers import admins_router, auth_router
from umbrella_server.domains.instance.router import instance_router
from umbrella_server.domains.agents.routers import agents_router, agent_router, enrollment_tokens_router
from umbrella_server.domains.groups.routers import groups_router
from umbrella_server.domains.policies.routers import policies_router, services_router
from umbrella_server.domains.commands.routers import commands_router
from umbrella_server.domains.metrics.routers import metrics_router
from umbrella_server.domains.processes.routers import processes_router
from umbrella_server.domains.agents.routers.stream import stream_router
from umbrella_server.domains.audit.routers import audit_router
from umbrella_server.domains.releases.routers import admin_releases_router, agent_releases_router
from umbrella_server.shared.sse_broker import agent_broker, GLOBAL_KEY


async def _stale_agent_loop(
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    """Фоновая задача: каждые 15 с переводит молчащих агентов в disabled."""
    logger = get_logger("stale_agent_checker")
    from datetime import UTC, datetime, timedelta
    while True:
        await asyncio.sleep(15)
        try:
            async with factory() as session:
                repo = AgentRepository(session)
                cutoff = datetime.now(UTC) - timedelta(seconds=settings.agent_offline_timeout_sec)
                count = await repo.mark_stale_offline(cutoff)
                if count:
                    await session.commit()
                    logger.info("agents_marked_offline", count=count)
                    await agent_broker.publish(GLOBAL_KEY, "agents_refresh", {})
        except Exception as exc:  # noqa: BLE001
            logger.error("stale_agent_check_failed", error=str(exc))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger = get_logger(__name__)
    settings = get_settings()
    logger.info("app_started", env=settings.env.value, debug=settings.debug)

    # Инициализация instance
    container = app.state.dishka_container
    factory = await container.get(async_sessionmaker[AsyncSession])
    await ensure_instance(factory)

    # Eager-инициализация PKI CA (генерирует если файлов нет)
    if settings.pki_ca_cert_path and settings.pki_ca_key_path:
        try:
            ca = BranchCA.ensure(
                cert_path=settings.pki_ca_cert_path,
                key_path=settings.pki_ca_key_path,
                branch_name="Umbrella",
            )
            logger.info("pki_ready", expires=ca.cert_expires_at.isoformat())
        except Exception as exc:
            logger.error("pki_init_failed", error=str(exc))
    else:
        logger.warning("pki_not_configured", hint="Set SERVER_PKI_CA_CERT_PATH and SERVER_PKI_CA_KEY_PATH")

    stale_task = asyncio.create_task(
        _stale_agent_loop(factory, settings),
        name="stale_agent_checker",
    )

    yield

    stale_task.cancel()
    try:
        await stale_task
    except asyncio.CancelledError:
        pass

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
    app.include_router(instance_router)
    app.include_router(agents_router)
    app.include_router(agent_router)
    app.include_router(enrollment_tokens_router)
    app.include_router(groups_router)
    app.include_router(policies_router)
    app.include_router(services_router)
    app.include_router(commands_router)
    app.include_router(metrics_router)
    app.include_router(processes_router)
    app.include_router(stream_router)
    app.include_router(audit_router)
    app.include_router(admin_releases_router)
    app.include_router(agent_releases_router)

    return app


app = create_app()
