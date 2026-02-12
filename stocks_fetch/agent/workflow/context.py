"""Runtime context passed into node builders."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.mcp_client import AgentMCPClient
from stocks_fetch.agent.models.base import ModelGateway


@dataclass(frozen=True)
class WorkflowContext:
    """Dependencies shared by all node handlers."""

    config: AgentConfig
    mcp: AgentMCPClient
    progress: Callable[[str], None]
    model_gateway: ModelGateway
