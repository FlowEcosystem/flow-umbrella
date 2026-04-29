"""Agent-facing API: enrollment, heartbeat, policy polling, commands."""

from typing import Annotated
from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, status

from umbrella_server.core.config import Settings
from umbrella_server.domains.agents.dependencies import current_agent
from umbrella_server.domains.agents.models import Agent
from umbrella_server.domains.agents.schemas import (
    AgentEnrollRequest,
    AgentEnrollResponse,
    AgentHeartbeatRequest,
    AgentRead,
    AgentRenewRequest,
    AgentRenewResponse,
)
from umbrella_server.domains.agents.service import AgentService
from umbrella_server.domains.audit.service import AuditService
from umbrella_server.pki.decommission_key import DecommissionKey
from umbrella_server.domains.commands.schemas import AgentCommandItem, AgentCommandResultRequest, CommandRead
from umbrella_server.domains.commands.service import CommandService
from umbrella_server.domains.policies.schemas import AgentPolicyItem
from umbrella_server.domains.policies.service import PolicyService
from umbrella_server.domains.metrics.schemas import AgentMetricPush
from umbrella_server.domains.metrics.service import MetricsService
from umbrella_server.domains.processes.schemas import AgentProcessPush
from umbrella_server.domains.processes.service import ProcessService
from umbrella_server.shared.sse_broker import agent_broker, GLOBAL_KEY

_DANGEROUS_PROCESSES = {
    "xray.exe", "v2ray.exe", "sing-box.exe", "trojan.exe",
    "shadowsocks.exe", "clash.exe", "tor.exe", "torbrowser.exe",
    "openvpn.exe", "wireguard.exe", "ngrok.exe", "frpc.exe",
    "proxifier.exe", "mimikatz.exe", "procdump.exe", "psexec.exe",
}

agent_router = APIRouter(prefix="/v1/agent", tags=["agent"])


@agent_router.post(
    "/enroll",
    response_model=AgentEnrollResponse,
    status_code=status.HTTP_200_OK,
)
@inject
async def enroll(
    payload: AgentEnrollRequest,
    service: FromDishka[AgentService],
    settings: FromDishka[Settings],
    decommission_key: FromDishka[DecommissionKey | None],
    audit: FromDishka[AuditService],
) -> AgentEnrollResponse:
    agent, raw_token, cert_pem, ca_cert_pem = await service.enroll(
        enrollment_token=payload.enrollment_token,
        csr_pem=payload.csr_pem.encode("utf-8"),
        hostname=payload.hostname,
        os=payload.os,
        os_version=payload.os_version,
        agent_version=payload.agent_version,
        ip_address=payload.ip_address,
    )
    await audit.log(
        "agent.enrolled",
        entity_type="agent",
        entity_id=str(agent.id),
        details={"hostname": payload.hostname, "os": payload.os, "ip": payload.ip_address},
    )
    return AgentEnrollResponse(
        agent_id=agent.id,
        agent_token=raw_token,
        cert_pem=cert_pem.decode("utf-8"),
        ca_cert_pem=ca_cert_pem.decode("utf-8"),
        cert_expires_at=agent.cert_expires_at,  # type: ignore[arg-type]
        policy_poll_interval_sec=settings.policy_poll_interval_sec,
        command_poll_interval_sec=settings.command_poll_interval_sec,
        metrics_push_interval_sec=settings.metrics_push_interval_sec,
        decommission_pubkey=decommission_key.public_key_pem() if decommission_key else None,
    )


@agent_router.post("/heartbeat", response_model=AgentRead)
@inject
async def heartbeat(
    payload: AgentHeartbeatRequest,
    agent: Annotated[Agent, Depends(current_agent)],
    service: FromDishka[AgentService],
) -> AgentRead:
    agent = await service.heartbeat(
        agent,
        os_version=payload.os_version,
        agent_version=payload.agent_version,
        ip_address=payload.ip_address,
    )
    read = AgentRead.model_validate(agent)
    data = read.model_dump()
    await agent_broker.publish(str(agent.id), "agent", data)
    await agent_broker.publish(GLOBAL_KEY, "agent_update", data)
    return read


@agent_router.post("/renew", response_model=AgentRenewResponse)
@inject
async def renew_cert(
    payload: AgentRenewRequest,
    agent: Annotated[Agent, Depends(current_agent)],
    service: FromDishka[AgentService],
) -> AgentRenewResponse:
    cert_pem, ca_cert_pem = await service.renew_cert(
        agent, csr_pem=payload.csr_pem.encode("utf-8")
    )
    return AgentRenewResponse(
        cert_pem=cert_pem.decode("utf-8"),
        ca_cert_pem=ca_cert_pem.decode("utf-8"),
        cert_expires_at=agent.cert_expires_at,  # type: ignore[arg-type]
    )


@agent_router.get("/commands", response_model=list[AgentCommandItem])
@inject
async def poll_commands(
    agent: Annotated[Agent, Depends(current_agent)],
    command_service: FromDishka[CommandService],
) -> list[AgentCommandItem]:
    cmds = await command_service.poll_pending(agent.id)
    return [AgentCommandItem.model_validate(c) for c in cmds]


@agent_router.post("/commands/{command_id}/result", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def submit_command_result(
    command_id: UUID,
    payload: AgentCommandResultRequest,
    agent: Annotated[Agent, Depends(current_agent)],
    command_service: FromDishka[CommandService],
) -> None:
    cmd = await command_service.submit_result(
        command_id,
        agent.id,
        status=payload.status,
        result=payload.result,
        error_message=payload.error_message,
    )
    await agent_broker.publish(
        str(agent.id), "command", CommandRead.model_validate(cmd).model_dump(),
    )


@agent_router.get("/policies", response_model=list[AgentPolicyItem])
@inject
async def get_agent_policies(
    agent: Annotated[Agent, Depends(current_agent)],
    policy_service: FromDishka[PolicyService],
) -> list[AgentPolicyItem]:
    policies = await policy_service.get_policies_for_agent(agent.id)
    result = []
    for p in policies:
        all_rules = list(p.custom_rules or [])
        for svc in (p.services or []):
            all_rules.extend(svc.rules or [])
        result.append(AgentPolicyItem(
            id=p.id,
            name=p.name,
            kind=p.kind,
            action=p.action,
            version=p.version,
            rules=all_rules,
        ))
    return result


@agent_router.post("/metrics", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def push_metrics(
    payload: AgentMetricPush,
    agent: Annotated[Agent, Depends(current_agent)],
    metrics_service: FromDishka[MetricsService],
) -> None:
    await metrics_service.push(agent, payload)
    await agent_broker.publish(str(agent.id), "metrics", {
        "collected_at": payload.collected_at.isoformat(),
        "cpu_percent": payload.cpu_percent,
        "ram_used_mb": payload.ram_used_mb,
        "ram_total_mb": payload.ram_total_mb,
        "disk_used_gb": payload.disk_used_gb,
        "disk_total_gb": payload.disk_total_gb,
    })


@agent_router.post("/processes", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def push_processes(
    payload: AgentProcessPush,
    agent: Annotated[Agent, Depends(current_agent)],
    process_service: FromDishka[ProcessService],
) -> None:
    await process_service.push(agent, payload)
    await agent_broker.publish(str(agent.id), "processes", {
        "collected_at": payload.collected_at.isoformat(),
        "processes": [p.model_dump() for p in payload.processes],
    })
    for proc in payload.processes:
        if proc.name.lower() in _DANGEROUS_PROCESSES:
            alert = {
                "agent_id": str(agent.id),
                "hostname": agent.hostname,
                "process_name": proc.name,
                "detected_at": payload.collected_at.isoformat(),
            }
            await agent_broker.publish(str(agent.id), "alert", alert)
            await agent_broker.publish(GLOBAL_KEY, "alert", alert)
