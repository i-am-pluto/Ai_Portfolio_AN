"""LangGraph workflow state definition for portfolio analysis."""

from __future__ import annotations

from typing import Any, TypedDict


class ToolSpec(TypedDict, total=False):
    """Normalized metadata for discovered MCP tools."""

    name: str
    description: str
    input_schema: dict[str, Any]


class WorkflowState(TypedDict, total=False):
    """State for portfolio analysis workflow."""

    run_id: str
    started_at: str
    updated_at: str
    current_node: str
    completed_nodes: list[str]
    user_request: str
    auth_status: str
    kite_login_url: str
    kite_login_result: Any
    kite_connected: bool
    degraded_mode: bool
    halted: bool
    tools_catalog: dict[str, list[ToolSpec]]
    holdings: list[dict[str, Any]]
    symbols: list[str]
    per_symbol_analysis: dict[str, dict[str, Any]]
    peer_comparison: list[dict[str, Any]] | str
    correlation_data: dict[str, Any] | str
    portfolio_insights: str
    executive_summary: str
    data_status: dict[str, dict[str, str]]
    report_path: str
    errors: list[str]
