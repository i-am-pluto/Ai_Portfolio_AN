"""Discover-tools workflow node."""

from __future__ import annotations

from stocks_fetch.agent.state.schema import ToolSpec, WorkflowState
from stocks_fetch.agent.workflow.context import WorkflowContext
from stocks_fetch.agent.workflow.helpers.state_updates import init_next_state
from stocks_fetch.agent.workflow.helpers.tools import discover_server_tools


def build_discover_tools_node(ctx: WorkflowContext):
    """Build node that discovers tool catalogs for each server."""

    async def discover_tools_node(state: WorkflowState) -> WorkflowState:
        ctx.progress("[2/6] Discovering available tools...")
        next_state = init_next_state(state)
        catalog: dict[str, list[ToolSpec]] = {}

        catalog["stock-analyzer"] = await discover_server_tools(
            mcp=ctx.mcp,
            server="stock-analyzer",
            state=next_state,
        )

        if ctx.mcp.kite_connected:
            catalog["kite"] = await discover_server_tools(
                mcp=ctx.mcp,
                server="kite",
                state=next_state,
            )
        else:
            catalog["kite"] = []

        next_state["tools_catalog"] = catalog
        return next_state

    return discover_tools_node
