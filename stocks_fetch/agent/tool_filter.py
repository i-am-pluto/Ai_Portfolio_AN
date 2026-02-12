"""Safety filtering for MCP tools to enforce strict Kite read-only usage."""

from __future__ import annotations

import re

_RISKY_KITE_KEYWORDS = {
    "buy",
    "sell",
    "place",
    "modify",
    "cancel",
    "basket",
    "gtt",
    "exit",
    "squareoff",
    "convert",
}

_KITE_SAFE_TOOLS = {
    "login",
    "get_profile",
    "profile",
    "get_margins",
    "margins",
    "get_holdings",
    "holdings",
    "get_positions",
    "positions",
    "get_orders",
    "orders",
    "get_order_history",
    "order_history",
    "get_trades",
    "trades",
    "get_quote",
    "quote",
    "get_quotes",
    "quotes",
    "get_ltp",
    "ltp",
    "get_ohlc",
    "ohlc",
    "get_historical_data",
    "historical_data",
    "get_instruments",
    "instruments",
    "search_instruments",
    "get_mf_holdings",
    "mf_holdings",
}

_STOCK_ANALYZER_SAFE_TOOLS = {
    "get_fundamental_ratios",
    "get_financial_statements",
    "get_peer_comparison",
    "get_dividends_and_splits",
    "get_nse_corporate_actions",
    "get_stock_news",
    "get_stock_correlations",
}


def _normalize_tool_name(tool_name: str) -> str:
    """Normalize tool names to lowercase underscore format for matching."""
    return re.sub(r"[^a-z0-9]+", "_", tool_name.strip().lower()).strip("_")


def is_tool_allowed(tool_name: str, mcp_name: str) -> bool:
    """Check if a tool is allowed to execute under the given MCP safety policy."""
    normalized_name = _normalize_tool_name(tool_name)
    normalized_mcp = _normalize_tool_name(mcp_name)

    if normalized_mcp == "kite":
        if any(keyword in normalized_name for keyword in _RISKY_KITE_KEYWORDS):
            return False
        return normalized_name in _KITE_SAFE_TOOLS

    if normalized_mcp == "stock_analyzer":
        return normalized_name in _STOCK_ANALYZER_SAFE_TOOLS

    return False


def get_safe_kite_tools() -> set[str]:
    """Get the strict allowlist of safe Kite tools."""
    return set(_KITE_SAFE_TOOLS)


def get_safe_stock_analyzer_tools() -> set[str]:
    """Get the strict allowlist of safe stock-analyzer tools."""
    return set(_STOCK_ANALYZER_SAFE_TOOLS)
