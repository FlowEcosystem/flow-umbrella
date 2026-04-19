from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from umbrella_server.core.exceptions import (
    AlreadyExistsError,
    ConflictError,
    DomainError,
    NotFoundError,
    UmbrellaError,
    ValidationError,
)
from umbrella_server.core.logging import get_logger
from umbrella_server.domains.auth.exceptions import (
    AdminInactiveError,
    InsufficientPermissionsError,
    InvalidCredentialsError,
    RefreshTokenRevokedError,
    TokenExpiredError,
    TokenInvalidError,
)

logger = get_logger(__name__)


_STATUS_MAP: dict[type[UmbrellaError], int] = {
    InvalidCredentialsError: 401,
    TokenInvalidError: 401,
    TokenExpiredError: 401,
    RefreshTokenRevokedError: 401,
    AdminInactiveError: 401,
    InsufficientPermissionsError: 403,
    NotFoundError: 404,
    AlreadyExistsError: 409,
    ConflictError: 409,
    ValidationError: 422,
    DomainError: 400,
}


def _status_for(exc: UmbrellaError) -> int:
    for klass in type(exc).__mro__:
        if klass in _STATUS_MAP:
            return _STATUS_MAP[klass]
    return 500


def _format_validation_errors(errors: list[dict]) -> list[dict]:
    """Преобразует raw-ошибки Pydantic в наш формат.

    loc у pydantic: ('body', 'email') → field: 'body.email'
    """
    formatted: list[dict] = []
    for err in errors:
        loc = err.get("loc", ())
        # Первый элемент обычно 'body'/'query'/'path' — убираем для краткости,
        # но оставляем если поле вложено ('body',) без продолжения.
        if len(loc) > 1:
            field = ".".join(str(p) for p in loc[1:])
        else:
            field = ".".join(str(p) for p in loc) or "root"
        formatted.append(
            {
                "field": field,
                "type": err.get("type", "unknown"),
                "message": err.get("msg", ""),
            }
        )
    return formatted


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(UmbrellaError)
    async def _handle_umbrella(request: Request, exc: UmbrellaError) -> JSONResponse:
        status_code = _status_for(exc)
        if status_code >= 500:
            logger.error(
                "unhandled_umbrella_error",
                path=request.url.path,
                **exc.to_dict(),
                exc_info=exc,
            )
        else:
            logger.warning(
                "domain_error",
                path=request.url.path,
                status=status_code,
                **exc.to_dict(),
            )
        return JSONResponse(status_code=status_code, content=exc.to_dict())

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = _format_validation_errors(exc.errors()) # pyright: ignore[reportArgumentType]
        logger.warning(
            "request_validation_failed",
            path=request.url.path,
            errors=errors,
        )
        return JSONResponse(
            status_code=422,
            content={
                "error_code": "request_validation_error",
                "message": "Request validation failed",
                "details": {"errors": errors},
            },
        )

    @app.exception_handler(HTTPException)
    async def _handle_http_exception(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        # Для случаев, когда кто-то всё же кинул HTTPException напрямую
        # (например, сторонние либы). Приводим к нашему формату.
        if exc.status_code >= 500:
            logger.error("http_exception_5xx", path=request.url.path, status=exc.status_code, detail=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": f"http_{exc.status_code}",
                "message": str(exc.detail) if exc.detail else "HTTP error",
                "details": {},
            },
        )