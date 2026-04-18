"""Настройка structlog для всего приложения."""

import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from umbrella_server.core.config import AppEnv, Settings


# Ширина колонки event-name.
_EVENT_COLUMN_WIDTH = 28


def _drop_color_message_key(_: Any, __: str, event_dict: EventDict) -> EventDict:
    event_dict.pop("color_message", None)
    return event_dict


def _pad_event_name(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """Выравнивает имя события и заменяет _ на пробелы для читаемости."""
    event = event_dict.get("event")
    if isinstance(event, str):
        event_dict["event"] = event.replace("_", " ").ljust(_EVENT_COLUMN_WIDTH)
    return event_dict

def _clean_logger_name(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """Чистит имя логгера: убирает __ вокруг dunder-имён и префикс пакета."""
    logger_name = event_dict.get("logger")
    if not isinstance(logger_name, str):
        return event_dict
    
    if logger_name.startswith("__") and logger_name.endswith("__"):
        logger_name = logger_name.strip("_")
    elif logger_name.startswith("umbrella_server."):
        logger_name = logger_name.removeprefix("umbrella_server.")
    
    event_dict["logger"] = logger_name
    return event_dict

def _build_shared_processors(env: AppEnv) -> list[Processor]:
    """Процессоры, общие для structlog и foreign-логов."""
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(
            fmt="%Y-%m-%d %H:%M:%S" if env is not AppEnv.prod else "iso",
            utc=True,
        ),
        structlog.processors.StackInfoRenderer(),
        _drop_color_message_key,
        _clean_logger_name
    ]
    if env is not AppEnv.prod:
        processors.append(_pad_event_name)
    return processors


def _build_renderer(env: AppEnv) -> Processor:
    if env is AppEnv.prod:
        return structlog.processors.JSONRenderer()
    return structlog.dev.ConsoleRenderer(
        colors=True,
        pad_level=True,
        sort_keys=True,
        exception_formatter=structlog.dev.RichTracebackFormatter(
            width=120,
            show_locals=False,
        ),
    )


def configure_logging(settings: Settings) -> None:
    shared_processors = _build_shared_processors(settings.env)
    renderer = _build_renderer(settings.env)
    log_level = logging.DEBUG if settings.debug else logging.INFO

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = [handler]
    root_logger.setLevel(log_level)

    for name in ("uvicorn.access", "sqlalchemy.engine", "httpx", "httpcore"):
        logging.getLogger(name).setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)