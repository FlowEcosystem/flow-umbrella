"""Global SSE stream for organisation-wide events (alerts, etc.)."""

import asyncio
from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from umbrella_server.domains.auth.service import AuthService
from umbrella_server.shared.sse_broker import GLOBAL_KEY, agent_broker

stream_router = APIRouter(prefix="/v1", tags=["stream"])


@stream_router.get("/stream")
@inject
async def global_stream(
    token: str,
    auth_service: FromDishka[AuthService],
) -> StreamingResponse:
    try:
        await auth_service.authenticate(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    q = agent_broker.subscribe(GLOBAL_KEY)

    async def generator():
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=25)
                    yield f"event: {msg['event']}\ndata: {msg['data']}\n\n"
                except asyncio.TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
        finally:
            agent_broker.unsubscribe(GLOBAL_KEY, q)

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
