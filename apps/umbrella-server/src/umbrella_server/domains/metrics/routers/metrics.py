"""Админский API метрик агентов."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Query

from umbrella_server.domains.auth.dependencies import current_any_admin
from umbrella_server.domains.auth.models import Admin
from umbrella_server.domains.metrics.schemas import AgentMetricRead
from umbrella_server.domains.metrics.service import MetricsService

metrics_router = APIRouter(prefix="/v1/agents/{agent_id}/metrics", tags=["metrics"])


@metrics_router.get("", response_model=list[AgentMetricRead])
@inject
async def get_agent_metrics(
    agent_id: UUID,
    _current: Annotated[Admin, Depends(current_any_admin)],
    service: FromDishka[MetricsService],
    limit: int = Query(default=60, ge=1, le=1440),
) -> list[AgentMetricRead]:
    items = await service.get_history(agent_id, limit)
    return [AgentMetricRead.model_validate(m) for m in items]
