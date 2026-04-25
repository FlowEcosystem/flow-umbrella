"""FastAPI-зависимости для agent-facing API."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from umbrella_server.core.config import Settings
from umbrella_server.domains.agents.exceptions import AgentTokenInvalidError
from umbrella_server.domains.agents.models import Agent
from umbrella_server.domains.agents.service import AgentService

_bearer_scheme = HTTPBearer(auto_error=False)

# nginx пробрасывает эти заголовки после успешной проверки client cert.
_HDR_CN       = "x-agent-cert-cn"
_HDR_VERIFIED = "x-agent-cert-verified"


def _extract_cn(dn: str) -> str | None:
    """Извлекает CN из Subject DN в формате RFC 2253.

    nginx передаёт $ssl_client_s_dn как RFC 2253 строку:
      "CN=agent:550e8400-...,O=Umbrella"  или просто  "CN=agent:550e8400-..."
    """
    for part in dn.split(","):
        part = part.strip()
        if part.upper().startswith("CN="):
            return part[3:]
    return None


@inject
async def current_agent(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    agent_service: FromDishka[AgentService],
    settings: FromDishka[Settings],
) -> Agent:
    if settings.agent_mtls:
        return await _auth_mtls(request, agent_service)
    return await _auth_bearer(credentials, agent_service)


async def _auth_mtls(request: Request, service: AgentService) -> Agent:
    """Читает cert CN из nginx-заголовка X-Agent-Cert-CN.

    nginx настроен так, что этот заголовок выставляется ТОЛЬКО если
    ssl_client_verify == SUCCESS. На порту 443 (admin API) эти заголовки
    явно зачищаются в proxy_set_header, поэтому подделка невозможна.
    """
    verified = request.headers.get(_HDR_VERIFIED, "")
    if verified != "SUCCESS":
        raise AgentTokenInvalidError()

    # DN от nginx: "CN=agent:550e8400-...,O=Umbrella" (RFC 2253)
    # или просто "CN=agent:550e8400-..." если в cert только CN.
    dn = request.headers.get(_HDR_CN, "").strip()
    cn = _extract_cn(dn)
    if cn is None or not cn.startswith("agent:"):
        raise AgentTokenInvalidError()

    try:
        agent_id = UUID(cn.removeprefix("agent:"))
    except ValueError:
        raise AgentTokenInvalidError()

    return await service.authenticate_by_cert(agent_id)


async def _auth_bearer(
    credentials: HTTPAuthorizationCredentials | None,
    service: AgentService,
) -> Agent:
    """Dev-fallback: Bearer token без nginx."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AgentTokenInvalidError()
    return await service.authenticate(credentials.credentials)
