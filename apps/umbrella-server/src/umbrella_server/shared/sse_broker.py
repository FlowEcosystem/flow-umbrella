"""In-process SSE pub/sub broker for agent real-time events.

Works for single-process uvicorn deployments. For multi-worker setups
Redis pub/sub would be needed instead.
"""

import asyncio
import json
from collections import defaultdict
from typing import Any


class AgentSSEBroker:
    def __init__(self) -> None:
        self._channels: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, agent_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._channels[agent_id].append(q)
        return q

    def unsubscribe(self, agent_id: str, q: asyncio.Queue) -> None:
        try:
            self._channels[agent_id].remove(q)
        except ValueError:
            pass

    async def publish(self, agent_id: str, event: str, data: Any) -> None:
        if not self._channels.get(agent_id):
            return
        payload = json.dumps(data, default=str)
        msg = {"event": event, "data": payload}
        dead = []
        for q in list(self._channels[agent_id]):
            try:
                q.put_nowait(msg)
            except asyncio.QueueFull:
                dead.append(q)
        for q in dead:
            self.unsubscribe(agent_id, q)


agent_broker = AgentSSEBroker()

# Special key for organisation-wide events (e.g. dangerous process alerts).
GLOBAL_KEY = "__global__"
