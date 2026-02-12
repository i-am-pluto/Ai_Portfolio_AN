"""Base protocol types for pluggable LLM gateways."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from stocks_fetch.agent.config import AgentConfig


class ModelGateway(Protocol):
    """Unified text-generation gateway used by workflow nodes."""

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        """Return model output for a system + user prompt pair."""


ProviderBuilder = Callable[[AgentConfig], ModelGateway]
