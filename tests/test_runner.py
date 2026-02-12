"""Tests for runner behavior in one-shot and conversational paths."""

from __future__ import annotations

import asyncio
from pathlib import Path

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent import runner


class _DummyMCPClient:
    async def __aenter__(self):  # type: ignore[no-untyped-def]
        return self

    async def __aexit__(self, exc_type, exc, tb):  # type: ignore[no-untyped-def]
        return None


def test_run_agent_loop_auto_analysis_default_request(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    captured = {"request": "unexpected"}

    async def _fake_run_analysis_once(config, mcp, user_request=None, on_progress=None):  # type: ignore[no-untyped-def]
        captured["request"] = user_request
        return {
            "report_path": str(tmp_path / "portfolio_analysis_2026-02-11.md"),
            "errors": [],
            "executive_summary": "",
        }

    monkeypatch.setattr(runner, "run_analysis_once", _fake_run_analysis_once)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)

    exit_code = asyncio.run(
        runner.run_agent_loop(
            config,
            one_shot=True,
            mcp_client_factory=lambda cfg: _DummyMCPClient(),
            output_func=lambda _: None,
        )
    )

    assert exit_code == 0
    assert captured["request"] is None


def test_run_agent_loop_enters_conversation_after_report(
    monkeypatch, tmp_path: Path
) -> None:  # type: ignore[no-untyped-def]
    outputs: list[str] = []
    prompts: list[str] = []

    async def _fake_run_analysis_once(config, mcp, user_request=None, on_progress=None):  # type: ignore[no-untyped-def]
        return {
            "report_path": str(tmp_path / "portfolio_analysis_2026-02-11.md"),
            "errors": [],
            "executive_summary": "Exec summary",
        }

    def _fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return "exit"

    monkeypatch.setattr(runner, "run_analysis_once", _fake_run_analysis_once)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)

    exit_code = asyncio.run(
        runner.run_agent_loop(
            config,
            one_shot=False,
            input_func=_fake_input,
            output_func=outputs.append,
            mcp_client_factory=lambda cfg: _DummyMCPClient(),
        )
    )

    assert exit_code == 0
    assert any("Report saved to:" in line for line in outputs)
    assert any("Entering conversational mode" in line for line in outputs)
    assert prompts == ["portfolio-agent> "]


def test_run_agent_loop_waits_for_manual_kite_login_then_continues(
    monkeypatch, tmp_path: Path
) -> None:  # type: ignore[no-untyped-def]
    outputs: list[str] = []
    prompts: list[str] = []
    call_count = {"n": 0}

    async def _fake_run_analysis_once(config, mcp, user_request=None, on_progress=None):  # type: ignore[no-untyped-def]
        call_count["n"] += 1
        if call_count["n"] == 1:
            return {
                "auth_status": "kite_login_required",
                "kite_login_url": "https://kite.example/login",
                "halted": True,
                "report_path": "",
                "errors": [],
                "executive_summary": "",
            }
        return {
            "auth_status": "kite_authenticated",
            "halted": False,
            "report_path": str(tmp_path / "portfolio_analysis_2026-02-11.md"),
            "errors": [],
            "executive_summary": "",
        }

    def _fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return ""

    monkeypatch.setattr(runner, "run_analysis_once", _fake_run_analysis_once)
    # Use 0 delay in tests
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path, auth_retry_delay=0.0)

    exit_code = asyncio.run(
        runner.run_agent_loop(
            config,
            one_shot=True,
            input_func=_fake_input,
            output_func=outputs.append,
            mcp_client_factory=lambda cfg: _DummyMCPClient(),
        )
    )

    assert exit_code == 0
    assert call_count["n"] == 2
    assert any("Kite login is required" in line for line in outputs)
    assert any("https://kite.example/login" in line for line in outputs)
    assert any("Waiting for session to activate" in line for line in outputs)
    assert prompts == ["Press Enter after successful Kite login (or type 'exit' to quit): "]


def test_run_agent_loop_prints_login_payload_when_url_missing(
    monkeypatch, tmp_path: Path
) -> None:  # type: ignore[no-untyped-def]
    outputs: list[str] = []
    prompts: list[str] = []
    call_count = {"n": 0}

    async def _fake_run_analysis_once(config, mcp, user_request=None, on_progress=None):  # type: ignore[no-untyped-def]
        call_count["n"] += 1
        if call_count["n"] == 1:
            return {
                "auth_status": "kite_login_pending",
                "kite_login_result": {"message": "open browser auth flow"},
                "halted": True,
                "report_path": "",
                "errors": [],
                "executive_summary": "",
            }
        return {
            "auth_status": "kite_authenticated",
            "halted": False,
            "report_path": str(tmp_path / "portfolio_analysis_2026-02-11.md"),
            "errors": [],
            "executive_summary": "",
        }

    def _fake_input(prompt: str) -> str:
        prompts.append(prompt)
        return ""

    monkeypatch.setattr(runner, "run_analysis_once", _fake_run_analysis_once)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path, auth_retry_delay=0.0)

    exit_code = asyncio.run(
        runner.run_agent_loop(
            config,
            one_shot=True,
            input_func=_fake_input,
            output_func=outputs.append,
            mcp_client_factory=lambda cfg: _DummyMCPClient(),
        )
    )

    assert exit_code == 0
    assert call_count["n"] == 2
    assert any("URL parsing fallback" in line for line in outputs)
    assert any("open browser auth flow" in line for line in outputs)
    assert prompts == ["Press Enter after successful Kite login (or type 'exit' to quit): "]
