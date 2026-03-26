"""MCP tools for triggering full portfolio analysis and checking Kite auth status."""

from __future__ import annotations

import os
from typing import Any

from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    """Register workflow trigger tools onto the MCP server instance."""

    @mcp.tool()
    async def get_kite_auth_status() -> dict[str, Any]:
        """
        Check Zerodha Kite MCP connection and authentication status.

        ALWAYS call this before trigger_portfolio_analysis to confirm the user's
        Kite account is reachable and logged in. If authentication is required,
        share the login_url with the user and wait for them to complete Zerodha
        2FA in their browser before retrying.

        Returns:
            connected (bool): Whether the Kite MCP SSE endpoint is reachable.
            authenticated (bool): Whether the Zerodha session is active.
            login_url (str | None): Browser URL for Zerodha 2FA (when not authenticated).
            message (str): Human-readable status description.
        """
        from dotenv import load_dotenv

        load_dotenv(override=False)

        from stocks_fetch.agent.config import AgentConfig
        from stocks_fetch.agent.mcp_client import AgentMCPClient

        try:
            config = AgentConfig.from_env(require_model_key=False)
        except Exception as exc:
            return {
                "connected": False,
                "authenticated": False,
                "login_url": None,
                "message": f"Server configuration error: {exc}",
            }

        kite_url = config.kite_sse_url
        # Derive the Kite login page URL from the SSE endpoint.
        login_url = kite_url.replace("/sse", "") if kite_url.endswith("/sse") else kite_url

        async with AgentMCPClient(kite_sse_url=kite_url, use_kite=True) as client:
            if not client.kite_connected:
                return {
                    "connected": False,
                    "authenticated": False,
                    "login_url": None,
                    "message": (
                        f"Kite MCP is not reachable at {kite_url}. "
                        "Ensure the Kite MCP service is running and the URL is correct. "
                        "Check your KITE_SSE_URL environment variable."
                    ),
                }

            # Probe for a holdings/portfolio tool to verify session validity.
            holding_tool = await client.find_tool_name(
                "kite",
                preferred_names=["holdings", "get_holdings", "portfolio", "positions"],
                fuzzy_keywords=["holding"],
            )

            if not holding_tool:
                return {
                    "connected": True,
                    "authenticated": False,
                    "login_url": login_url,
                    "message": (
                        "Kite MCP is reachable but no portfolio tools were found. "
                        f"Please log in via: {login_url}"
                    ),
                }

            try:
                await client.call_tool("kite", holding_tool, {})
                return {
                    "connected": True,
                    "authenticated": True,
                    "login_url": None,
                    "message": (
                        "Kite MCP is connected and authenticated. "
                        "Live portfolio holdings are available."
                    ),
                }
            except RuntimeError as exc:
                err = str(exc).lower()
                if any(k in err for k in ("401", "unauthorized", "login", "auth", "session")):
                    return {
                        "connected": True,
                        "authenticated": False,
                        "login_url": login_url,
                        "message": (
                            "Kite is connected but your Zerodha session has expired. "
                            f"Please open this URL and complete 2FA login: {login_url}"
                        ),
                    }
                return {
                    "connected": True,
                    "authenticated": False,
                    "login_url": None,
                    "message": f"Kite probe failed with unexpected error: {exc}",
                }

    @mcp.tool()
    async def trigger_portfolio_analysis(
        request: str = "Full portfolio analysis with actionable recommendations",
        use_kite: bool = True,
        symbols: list[str] | None = None,
    ) -> str:
        """
        Run the full automated LangGraph portfolio analysis pipeline and return the report.

        This tool orchestrates a 6-node workflow:
          1. Authenticate — verify Kite connection
          2. Discover tools — catalogue available MCP capabilities
          3. Fetch holdings — pull live positions from Zerodha demat account
          4. Gather data — fetch fundamentals, news, dividends, correlations per symbol
          5. Generate insights — LLM analysis of portfolio health and risks
          6. Write report — produce structured markdown report

        IMPORTANT: Call get_kite_auth_status() first.
        - If connected=false or authenticated=false, ask the user to connect/login before running.
        - If authenticated=true, proceed directly.

        Args:
            request: Natural language focus for the analysis
                     (e.g. "Focus on dividend yield and downside risk").
            use_kite: Set True (default) to fetch live holdings from the user's Zerodha
                      demat account. Set False to analyse only the symbols list provided.
            symbols: NSE symbols to analyse when use_kite=False, or to supplement
                     live holdings (e.g. ["RELIANCE", "TCS", "INFY"]).

        Returns:
            Full markdown portfolio analysis report including per-stock observations,
            correlation matrix, and actionable recommendations.
        """
        from dotenv import load_dotenv

        load_dotenv(override=False)

        backend_name = os.environ.get("AI_BACKEND", "langgraph")

        try:
            from stocks_fetch.agent.backends.registry import get_backend

            backend = get_backend(backend_name)
            report = await backend.run_analysis(
                request=request,
                use_kite=use_kite,
                symbols=symbols or [],
            )
            return report
        except Exception as exc:
            return (
                f"# Portfolio Analysis Failed\n\n"
                f"**Error**: {exc}\n\n"
                f"**Suggested steps**:\n"
                f"1. Call `get_kite_auth_status()` to verify Kite connectivity.\n"
                f"2. If Kite is not authenticated, share the login URL with the user.\n"
                f"3. After login, retry `trigger_portfolio_analysis()`.\n"
                f"4. To run without live holdings: "
                f"`trigger_portfolio_analysis(use_kite=false, symbols=['RELIANCE', 'TCS'])`"
            )
