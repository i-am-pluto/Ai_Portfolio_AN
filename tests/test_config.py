"""Tests for environment-driven agent configuration."""

from __future__ import annotations

import pytest

from stocks_fetch.agent.config import AgentConfig


def test_from_env_requires_groq_key_when_provider_is_groq(monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        AgentConfig.from_env(require_model_key=True)


def test_from_env_accepts_grok_with_grok_api_key(monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("LLM_PROVIDER", "grok")
    monkeypatch.setenv("GROK_API_KEY", "test-key")
    monkeypatch.setenv("GROK_MODEL", "grok-test-model")

    cfg = AgentConfig.from_env(require_model_key=True)

    assert cfg.llm_provider == "grok"
    assert cfg.grok_api_key == "test-key"
    assert cfg.grok_model == "grok-test-model"


def test_from_env_accepts_xai_api_key_alias(monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("LLM_PROVIDER", "xai")
    monkeypatch.delenv("GROK_API_KEY", raising=False)
    monkeypatch.setenv("XAI_API_KEY", "alias-key")

    cfg = AgentConfig.from_env(require_model_key=True)

    assert cfg.llm_provider == "xai"
    assert cfg.grok_api_key == "alias-key"


def test_from_env_rejects_unknown_provider(monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("LLM_PROVIDER", "invalid-provider")

    with pytest.raises(ValueError, match="LLM_PROVIDER"):
        AgentConfig.from_env(require_model_key=False)
