"""Tests for LangGraph workflow behavior."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.workflow.errors import (
    _is_auth_error,
    _is_transient_error,
    _sanitize_error,
)
from stocks_fetch.agent.workflow.graph import create_analysis_workflow


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeLLM:
    def __init__(self) -> None:
        self._calls = 0

    def invoke(self, messages: list[Any]) -> _FakeResponse:
        self._calls += 1
        if self._calls == 1:
            return _FakeResponse("Detailed portfolio insights.")
        return _FakeResponse("- Summary bullet 1\n- Summary bullet 2")


class _FakeMCP:
    """Mock MCP client supporting lazy auth pattern.

    When `pre_authenticated=False`, calls to get_holdings raise "unauthorized"
    to trigger the lazy auth flow in fetch_portfolio_context_node.
    """

    def __init__(self, kite_connected: bool = True, pre_authenticated: bool = False) -> None:
        self.kite_connected = kite_connected
        self.kite_error = None if kite_connected else "offline"
        self.authenticated = pre_authenticated
        self.calls: list[tuple[str, str, dict[str, Any]]] = []

    async def find_tool_name(
        self,
        server: str,
        preferred_names: list[str] | None = None,
        fuzzy_keywords: list[str] | None = None,
        refresh: bool = False,
    ) -> str | None:
        if server == "kite" and self.kite_connected:
            preferred_names = preferred_names or []
            for name in preferred_names:
                if name == "login":
                    return "login"
            return None
        return None

    async def list_tools(self, server: str, refresh: bool = False) -> list[dict[str, Any]]:
        if server == "stock-analyzer":
            return [
                {"name": "get_fundamental_ratios", "description": "", "input_schema": {}},
                {"name": "get_dividends_and_splits", "description": "", "input_schema": {}},
                {"name": "get_nse_corporate_actions", "description": "", "input_schema": {}},
                {"name": "get_stock_news", "description": "", "input_schema": {}},
                {"name": "get_peer_comparison", "description": "", "input_schema": {}},
                {"name": "get_stock_correlations", "description": "", "input_schema": {}},
            ]
        if not self.kite_connected:
            return []
        return [
            {"name": "login", "description": "", "input_schema": {}},
            {"name": "get_profile", "description": "", "input_schema": {}},
            {"name": "get_holdings", "description": "", "input_schema": {}},
        ]

    async def call_tool(self, server: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        self.calls.append((server, tool_name, arguments))
        if server == "kite" and tool_name == "login":
            return {"login_url": "https://kite.example/login"}
        if server == "kite" and tool_name == "get_holdings":
            if not self.authenticated:
                raise RuntimeError("unauthorized")
            return [{"tradingsymbol": "RELIANCE"}, {"tradingsymbol": "TCS"}]

        if tool_name == "get_fundamental_ratios":
            return {
                "symbol": arguments["symbol"],
                "valuation": {"pe_trailing": 22.0, "pb": 3.5},
                "profitability": {"roe": 0.18},
            }
        if tool_name == "get_dividends_and_splits":
            return {"dividends": [], "splits": []}
        if tool_name == "get_nse_corporate_actions":
            return []
        if tool_name == "get_stock_news":
            return []
        if tool_name == "get_peer_comparison":
            return []
        if tool_name == "get_stock_correlations":
            return {
                "symbols": ["RELIANCE", "TCS"],
                "correlation_matrix": [[1.0, 0.34], [0.34, 1.0]],
                "covariance_matrix": [[0.1, 0.02], [0.02, 0.12]],
            }
        return {}


def _run_async(coro):  # type: ignore[no-untyped-def]
    return asyncio.run(coro)


def _base_state() -> dict[str, Any]:
    return {
        "user_request": "Analyze",
        "auth_status": "pending",
        "kite_connected": False,
        "degraded_mode": False,
        "halted": False,
        "tools_catalog": {},
        "holdings": [],
        "symbols": [],
        "per_symbol_analysis": {},
        "peer_comparison": [],
        "correlation_data": {},
        "data_status": {},
        "portfolio_insights": "",
        "executive_summary": "",
        "report_path": "",
        "errors": [],
    }


# ---------------------------------------------------------------------------
# Lazy auth tests
# ---------------------------------------------------------------------------

def test_workflow_halts_at_fetch_with_login_url_when_auth_fails(tmp_path: Path) -> None:
    """With lazy auth, when get_holdings fails with 'unauthorized', the workflow
    triggers login and halts at fetch_portfolio_context with a login URL."""
    mcp = _FakeMCP(kite_connected=True, pre_authenticated=False)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)
    graph = create_analysis_workflow(config=config, mcp=mcp, llm_factory=lambda _: _FakeLLM())
    final_state = _run_async(graph.ainvoke(_base_state()))

    assert mcp.calls, "Expected at least one MCP call."
    # Should have tried get_holdings first (lazy), then triggered login
    assert any(call[1] == "get_holdings" for call in mcp.calls)
    assert any(call[1] == "login" for call in mcp.calls)
    assert final_state["auth_status"] == "kite_login_required"
    assert final_state["halted"] is True
    assert final_state.get("kite_login_url")
    assert not final_state.get("report_path")


def test_workflow_continues_when_kite_session_is_authenticated(tmp_path: Path) -> None:
    mcp = _FakeMCP(kite_connected=True, pre_authenticated=True)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)
    graph = create_analysis_workflow(config=config, mcp=mcp, llm_factory=lambda _: _FakeLLM())
    final_state = _run_async(graph.ainvoke(_base_state()))

    assert final_state["auth_status"] == "kite_authenticated"
    assert final_state.get("report_path")


def test_workflow_degraded_mode_when_kite_unavailable(tmp_path: Path) -> None:
    mcp = _FakeMCP(kite_connected=False)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)
    graph = create_analysis_workflow(config=config, mcp=mcp, llm_factory=lambda _: _FakeLLM())
    final_state = _run_async(graph.ainvoke(_base_state()))

    assert final_state["degraded_mode"] is True
    assert final_state["auth_status"] == "kite_unavailable"
    assert all(call[1] != "login" for call in mcp.calls)
    assert final_state.get("report_path")


def test_workflow_resumes_after_manual_login_on_same_mcp_session(tmp_path: Path) -> None:
    mcp = _FakeMCP(kite_connected=True, pre_authenticated=False)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)
    graph = create_analysis_workflow(config=config, mcp=mcp, llm_factory=lambda _: _FakeLLM())
    first_state = _run_async(graph.ainvoke(_base_state()))

    assert first_state["auth_status"] == "kite_login_required"
    assert first_state["halted"] is True

    mcp.authenticated = True
    second_state = _run_async(graph.ainvoke(_base_state()))

    assert second_state["auth_status"] == "kite_authenticated"
    assert second_state.get("report_path")


def test_workflow_extracts_login_url_from_free_text_payload(tmp_path: Path) -> None:
    class _TextLoginMCP(_FakeMCP):
        async def call_tool(self, server: str, tool_name: str, arguments: dict[str, Any]) -> Any:
            self.calls.append((server, tool_name, arguments))
            if server == "kite" and tool_name == "login":
                return {
                    "message": "Authenticate here: https://kite.example/login?request_id=abc123 ."
                }
            if server == "kite" and tool_name == "get_holdings":
                raise RuntimeError("unauthorized")
            return await super().call_tool(server, tool_name, arguments)

    mcp = _TextLoginMCP(kite_connected=True, pre_authenticated=False)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)
    graph = create_analysis_workflow(config=config, mcp=mcp, llm_factory=lambda _: _FakeLLM())
    final_state = _run_async(graph.ainvoke(_base_state()))

    assert final_state["auth_status"] == "kite_login_required"
    assert final_state["kite_login_url"] == "https://kite.example/login?request_id=abc123"


# ---------------------------------------------------------------------------
# Data status tracking tests
# ---------------------------------------------------------------------------

def test_workflow_populates_data_status_for_authenticated_session(tmp_path: Path) -> None:
    mcp = _FakeMCP(kite_connected=True, pre_authenticated=True)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)
    graph = create_analysis_workflow(config=config, mcp=mcp, llm_factory=lambda _: _FakeLLM())
    final_state = _run_async(graph.ainvoke(_base_state()))

    data_status = final_state.get("data_status", {})
    assert "RELIANCE" in data_status
    assert "TCS" in data_status
    assert data_status["RELIANCE"]["fundamental_ratios"] == "ok"
    assert data_status["TCS"]["stock_news"] == "ok"


# ---------------------------------------------------------------------------
# Error sanitization tests
# ---------------------------------------------------------------------------

def test_sanitize_error_strips_html_and_truncates() -> None:
    raw = "<html><body>Error: " + "x" * 300 + "</body></html>"
    cleaned = _sanitize_error(raw)
    assert "<html>" not in cleaned
    assert "<body>" not in cleaned
    assert len(cleaned) <= 203  # 200 + "..."
    assert cleaned.endswith("...")


def test_sanitize_error_preserves_short_clean_messages() -> None:
    msg = "Tool call failed: connection refused"
    assert _sanitize_error(msg) == msg


# ---------------------------------------------------------------------------
# Auth/transient error detection tests
# ---------------------------------------------------------------------------

def test_is_auth_error_detects_common_patterns() -> None:
    assert _is_auth_error(RuntimeError("unauthorized access"))
    assert _is_auth_error(RuntimeError("session expired"))
    assert _is_auth_error(RuntimeError("HTTP 401"))
    assert _is_auth_error(RuntimeError("HTTP 403 Forbidden"))
    assert not _is_auth_error(RuntimeError("connection timeout"))
    assert not _is_auth_error(RuntimeError("internal server error"))


def test_is_transient_error_detects_common_patterns() -> None:
    assert _is_transient_error(RuntimeError("connection timeout"))
    assert _is_transient_error(RuntimeError("HTTP 503 service unavailable"))
    assert _is_transient_error(RuntimeError("rate limit exceeded"))
    assert _is_transient_error(RuntimeError("HTTP 429"))
    assert not _is_transient_error(RuntimeError("unauthorized"))
    assert not _is_transient_error(RuntimeError("invalid argument"))


# ---------------------------------------------------------------------------
# Progress callback tests
# ---------------------------------------------------------------------------

def test_workflow_emits_progress_callbacks(tmp_path: Path) -> None:
    mcp = _FakeMCP(kite_connected=False)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)
    progress_messages: list[str] = []
    graph = create_analysis_workflow(
        config=config, mcp=mcp, llm_factory=lambda _: _FakeLLM(),
        on_progress=progress_messages.append,
    )
    _run_async(graph.ainvoke(_base_state()))

    assert any("[1/6]" in msg for msg in progress_messages)
    assert any("[2/6]" in msg for msg in progress_messages)
    assert any("[6/6]" in msg for msg in progress_messages)


def test_workflow_tracks_node_and_run_metadata(tmp_path: Path) -> None:
    mcp = _FakeMCP(kite_connected=False)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)
    graph = create_analysis_workflow(config=config, mcp=mcp, llm_factory=lambda _: _FakeLLM())
    final_state = _run_async(graph.ainvoke(_base_state()))

    assert final_state.get("run_id")
    assert final_state.get("started_at")
    assert final_state.get("updated_at")
    assert final_state.get("current_node") == "write_report"
    completed = final_state.get("completed_nodes", [])
    assert "authenticate_kite" in completed
    assert "write_report" in completed


# ---------------------------------------------------------------------------
# Tool validation tests
# ---------------------------------------------------------------------------

def test_workflow_skips_undiscovered_tools_gracefully(tmp_path: Path) -> None:
    """When stock-analyzer tools are partially discovered, missing tools
    should be marked as 'unavailable' rather than crashing."""

    class _PartialToolsMCP(_FakeMCP):
        async def list_tools(self, server: str, refresh: bool = False) -> list[dict[str, Any]]:
            if server == "stock-analyzer":
                # Only return 2 of the 4 per-symbol tools
                return [
                    {"name": "get_fundamental_ratios", "description": "", "input_schema": {}},
                    {"name": "get_stock_news", "description": "", "input_schema": {}},
                    {"name": "get_peer_comparison", "description": "", "input_schema": {}},
                    {"name": "get_stock_correlations", "description": "", "input_schema": {}},
                ]
            return await super().list_tools(server, refresh=refresh)

    mcp = _PartialToolsMCP(kite_connected=True, pre_authenticated=True)
    config = AgentConfig(groq_api_key="test", report_dir=tmp_path)
    graph = create_analysis_workflow(config=config, mcp=mcp, llm_factory=lambda _: _FakeLLM())
    final_state = _run_async(graph.ainvoke(_base_state()))

    data_status = final_state.get("data_status", {})
    assert data_status["RELIANCE"]["fundamental_ratios"] == "ok"
    assert data_status["RELIANCE"]["dividends_and_splits"] == "unavailable"
    assert data_status["RELIANCE"]["nse_corporate_actions"] == "unavailable"
    assert data_status["RELIANCE"]["stock_news"] == "ok"
    assert final_state.get("report_path")
