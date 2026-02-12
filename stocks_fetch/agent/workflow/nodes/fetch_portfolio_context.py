"""Fetch-portfolio-context workflow node."""

from __future__ import annotations

from stocks_fetch.agent.state.schema import WorkflowState
from stocks_fetch.agent.workflow.context import WorkflowContext
from stocks_fetch.agent.workflow.errors import append_error
from stocks_fetch.agent.workflow.helpers.auth import (
    fetch_kite_holdings,
    find_kite_portfolio_tools,
    transition_to_kite_login,
)
from stocks_fetch.agent.workflow.helpers.state_updates import init_next_state, reset_kite_context
from stocks_fetch.agent.workflow.helpers.symbols import extract_unique_symbols


def build_fetch_portfolio_context_node(ctx: WorkflowContext):
    """Build node that fetches holdings and resolves auth transition."""

    async def fetch_portfolio_context_node(state: WorkflowState) -> WorkflowState:
        ctx.progress("[3/6] Fetching portfolio holdings...")
        next_state = init_next_state(state)

        if not ctx.mcp.kite_connected:
            reset_kite_context(next_state)
            return next_state

        tools = next_state.get("tools_catalog", {}).get("kite", [])
        candidate_tools = find_kite_portfolio_tools(tools)
        holdings, auth_failure = await fetch_kite_holdings(
            mcp=ctx.mcp,
            state=next_state,
            candidate_tools=candidate_tools,
        )

        if auth_failure:
            return await transition_to_kite_login(next_state, ctx.mcp)

        next_state["auth_status"] = "kite_authenticated"
        symbols = extract_unique_symbols(holdings)

        next_state["holdings"] = holdings
        next_state["symbols"] = symbols

        if not symbols:
            append_error(
                next_state,
                "No holdings symbols found from Kite tools; "
                "report will be generated with available context.",
            )

        return next_state

    return fetch_portfolio_context_node
