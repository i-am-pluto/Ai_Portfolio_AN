"""Factory for building model gateways from config/registry."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.models.base import ModelGateway
from stocks_fetch.agent.models.providers import GroqModelGateway, XaiModelGateway
from stocks_fetch.agent.models.registry import get_provider, has_provider, register_provider


class _LegacyFactoryGateway(ModelGateway):
    """Adapter for legacy llm_factory(config)->model used by tests/injection."""

    def __init__(self, model: Any) -> None:
        self._model = model

    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self._model.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]
        )
        return response.content if isinstance(response.content, str) else str(response.content)


def _register_default_providers() -> None:
    if not has_provider("groq"):
        register_provider("groq", lambda config: GroqModelGateway(config))
    if not has_provider("grok"):
        register_provider("grok", lambda config: XaiModelGateway(config))
    if not has_provider("xai"):
        register_provider("xai", lambda config: XaiModelGateway(config))


def build_model_gateway(
    config: AgentConfig,
    llm_factory: Callable[[AgentConfig], Any] | None = None,
) -> ModelGateway:
    """Build a model gateway from injected factory or configured provider."""
    if llm_factory is not None:
        return _LegacyFactoryGateway(llm_factory(config))

    _register_default_providers()
    provider_builder = get_provider(config.llm_provider)
    return provider_builder(config)
