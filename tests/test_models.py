"""Tests for pluggable model registry/factory behavior."""

from __future__ import annotations

from typing import Any

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.models.factory import build_model_gateway
from stocks_fetch.agent.models.registry import register_provider


class _DummyResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _DummyLegacyModel:
    def invoke(self, messages: list[Any]) -> _DummyResponse:
        return _DummyResponse(f"received-{len(messages)}")


class _DummyGateway:
    def invoke_text(self, system_prompt: str, user_prompt: str) -> str:
        return f"{system_prompt}|{user_prompt}"


def test_build_model_gateway_supports_legacy_llm_factory_injection() -> None:
    cfg = AgentConfig(groq_api_key="test")
    gateway = build_model_gateway(cfg, llm_factory=lambda _: _DummyLegacyModel())
    result = gateway.invoke_text("system", "user")
    assert result == "received-2"


def test_build_model_gateway_supports_runtime_provider_registration() -> None:
    provider_name = "unit-test-provider"
    register_provider(provider_name, lambda _: _DummyGateway())

    cfg = AgentConfig(llm_provider=provider_name, groq_api_key="test")
    gateway = build_model_gateway(cfg)
    result = gateway.invoke_text("a", "b")
    assert result == "a|b"
