"""FastMCP server for Indian stock analysis — fundamentals, corporate actions & news."""

import os

from fastmcp import FastMCP

mcp = FastMCP(
    name="Indian Stock Analyzer",
    instructions=(
        "Analytical tools for Indian stocks — fundamentals, financial statements, "
        "peer comparison, corporate actions, news, and full portfolio analysis.\n\n"
        "## Kite MCP (Zerodha) — ALWAYS CHECK FIRST\n"
        "Before any portfolio analysis, verify Kite is connected and authenticated:\n"
        "1. Call `get_kite_auth_status` to check connection and login state.\n"
        "2. If `connected=false`: ask the user to ensure Kite MCP is running and "
        "reachable, then retry.\n"
        "3. If `connected=true` but `authenticated=false`: share the `login_url` "
        "with the user and ask them to complete Zerodha 2FA login in their browser, "
        "then call `get_kite_auth_status` again to confirm before proceeding.\n"
        "4. If `connected=true` and `authenticated=true`: proceed with analysis — "
        "holdings and symbols are fetched automatically from the user's demat account.\n\n"
        "## Triggering Full Analysis\n"
        "- `trigger_portfolio_analysis`: runs the complete 6-node LangGraph pipeline "
        "(holdings → fundamentals → correlations → insights → report). "
        "Returns the full markdown report. Requires Kite authenticated for live holdings; "
        "pass `use_kite=false` to run on provided symbols only.\n\n"
        "## Individual Stock Tools\n"
        "All NSE symbols (e.g., RELIANCE, TCS, HDFCBANK). No .NS suffix needed.\n"
        "- `get_fundamental_ratios`: PE, PB, ROE, margins, debt ratios\n"
        "- `get_financial_statements`: income/balance/cashflow statements\n"
        "- `get_peer_comparison`: side-by-side metrics for multiple stocks\n"
        "- `get_dividends_and_splits`: dividend history and stock splits\n"
        "- `get_nse_corporate_actions`: NSE announcements (bonus, rights, AGM)\n"
        "- `get_stock_news`: recent news articles\n"
        "- `get_stock_correlations`: pairwise correlation/covariance matrix"
    ),
)

# Each module exports a register(mcp) function that decorates tools onto this instance.
from stocks_fetch.sources.fundamentals import register as register_fundamentals
from stocks_fetch.sources.corporate import register as register_corporate
from stocks_fetch.sources.market_info import register as register_market_info
from stocks_fetch.sources.technical import register as register_technical
from stocks_fetch.sources.workflow_trigger import register as register_workflow_trigger

register_fundamentals(mcp)
register_corporate(mcp)
register_market_info(mcp)
register_technical(mcp)
register_workflow_trigger(mcp)


def main() -> None:
    """Entry point for console script — supports stdio (default) and SSE transports."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip().lower()
    if transport == "sse":
        host = os.environ.get("MCP_HOST", "0.0.0.0").strip()
        port = int(os.environ.get("MCP_PORT", os.environ.get("PORT", "8000")))
        mcp.run(transport="sse", host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
