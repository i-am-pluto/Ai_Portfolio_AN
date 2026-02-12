"""Analysis-data and enrichment helpers."""

from __future__ import annotations

import asyncio
from typing import Any

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.mcp_client import AgentMCPClient
from stocks_fetch.agent.state.schema import ToolSpec, WorkflowState
from stocks_fetch.agent.workflow.errors import _is_transient_error, append_error
from stocks_fetch.agent.workflow.helpers.tools import build_kite_symbol_args


async def call_tool_with_retry(
    mcp: AgentMCPClient,
    server: str,
    tool_name: str,
    args: dict[str, Any],
    delay: float = 2.0,
) -> Any:
    """Call a tool, retrying once after delay for transient errors."""
    try:
        return await mcp.call_tool(server, tool_name, args)
    except Exception as exc:
        if _is_transient_error(exc):
            await asyncio.sleep(delay)
            return await mcp.call_tool(server, tool_name, args)
        raise


_PER_SYMBOL_TOOL_PLAN: tuple[tuple[str, dict[str, Any]], ...] = (
    ("get_fundamental_ratios", {"symbol": "{symbol}"}),
    ("get_dividends_and_splits", {"symbol": "{symbol}"}),
    ("get_nse_corporate_actions", {"symbol": "{symbol}", "period": "1M"}),
    ("get_stock_news", {"symbol": "{symbol}", "count": 5}),
)


def _resolve_tool_args(template: dict[str, Any], symbol: str) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in template.items():
        if isinstance(value, str):
            resolved[key] = value.format(symbol=symbol)
        else:
            resolved[key] = value
    return resolved


async def collect_symbol_analysis(
    mcp: AgentMCPClient,
    state: WorkflowState,
    symbol: str,
    discovered_sa: set[str],
    retry_delay: float,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Collect stock-analyzer data for one symbol with availability tracking."""
    details: dict[str, Any] = {}
    status: dict[str, str] = {}

    for tool_name, template in _PER_SYMBOL_TOOL_PLAN:
        details_key = tool_name.replace("get_", "")
        if tool_name not in discovered_sa:
            status[details_key] = "unavailable"
            continue

        args = _resolve_tool_args(template, symbol)
        try:
            details[details_key] = await call_tool_with_retry(
                mcp,
                "stock-analyzer",
                tool_name,
                args,
                delay=retry_delay,
            )
            status[details_key] = "ok"
        except Exception as exc:
            status[details_key] = "failed"
            append_error(state, f"{symbol}: {tool_name} failed: {exc}")

    return details, status


async def collect_cross_symbol_metrics(
    mcp: AgentMCPClient,
    state: WorkflowState,
    symbols: list[str],
    discovered_sa: set[str],
    config: AgentConfig,
    retry_delay: float,
) -> None:
    """Fetch peer comparison and correlation metrics when symbol count allows."""
    if len(symbols) < 2:
        state["peer_comparison"] = []
        state["correlation_data"] = (
            "Need at least 2 symbols to compute correlation/covariance metrics."
        )
        return

    if "get_peer_comparison" in discovered_sa:
        try:
            state["peer_comparison"] = await call_tool_with_retry(
                mcp,
                "stock-analyzer",
                "get_peer_comparison",
                {"symbols": symbols},
                delay=retry_delay,
            )
        except Exception as exc:
            append_error(state, f"Peer comparison failed: {exc}")

    if "get_stock_correlations" not in discovered_sa:
        return

    try:
        state["correlation_data"] = await call_tool_with_retry(
            mcp,
            "stock-analyzer",
            "get_stock_correlations",
            {
                "symbols": symbols,
                "period": config.correlation_period,
                "interval": config.correlation_interval,
                "returns_type": config.correlation_returns_type,
                "annualize_covariance": True,
            },
            delay=retry_delay,
        )
    except Exception as exc:
        append_error(state, f"Correlation/covariance analysis failed: {exc}")


def _select_kite_secondary_tools(kite_tools: list[ToolSpec]) -> list[ToolSpec]:
    secondary_tools: list[ToolSpec] = []
    for tool in kite_tools:
        name = tool["name"].lower()
        if any(keyword in name for keyword in ("quote", "ltp", "ohlc")):
            secondary_tools.append(tool)
    return secondary_tools


async def enrich_with_kite_secondary(
    mcp: AgentMCPClient,
    per_symbol: dict[str, dict[str, Any]],
    symbols: list[str],
    kite_tools: list[ToolSpec],
) -> None:
    """Enrich per-symbol data using best-effort secondary Kite market tools."""
    secondary_tools = _select_kite_secondary_tools(kite_tools)
    for symbol in symbols:
        for tool in secondary_tools:
            args = build_kite_symbol_args(tool.get("input_schema", {}), symbol)
            if args is None:
                continue

            try:
                data = await mcp.call_tool("kite", tool["name"], args)
                per_symbol.setdefault(symbol, {}).setdefault("kite_secondary", {})[
                    tool["name"]
                ] = data
            except Exception:
                # Secondary enrichment is best-effort.
                continue


def fallback_insights(state: WorkflowState) -> str:
    """Deterministic fallback analysis when LLM is unavailable."""
    symbols = state.get("symbols", [])
    correlation_data = state.get("correlation_data", {})
    cluster_note = "Correlation data unavailable."
    if isinstance(correlation_data, dict):
        matrix = correlation_data.get("correlation_matrix", [])
        if isinstance(matrix, list) and matrix:
            strongest = 0.0
            for i, row in enumerate(matrix):
                if not isinstance(row, list):
                    continue
                for j, value in enumerate(row):
                    if i != j and isinstance(value, (int, float)):
                        strongest = max(strongest, abs(float(value)))
            cluster_note = (
                f"Highest observed pairwise correlation is {strongest:.2f}. "
                "Higher values indicate tighter diversification clusters."
            )
    return (
        f"Portfolio includes {len(symbols)} symbols: {', '.join(symbols) if symbols else 'none'}.\n"
        f"{cluster_note}\n"
        "Review concentration risk and compare fundamentals for any overweight positions."
    )
