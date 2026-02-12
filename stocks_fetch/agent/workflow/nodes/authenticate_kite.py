"""Authenticate-kite workflow node."""

from __future__ import annotations

from stocks_fetch.agent.state.schema import WorkflowState
from stocks_fetch.agent.workflow.context import WorkflowContext
from stocks_fetch.agent.workflow.errors import append_error
from stocks_fetch.agent.workflow.helpers.state_updates import init_next_state


def build_authenticate_kite_node(ctx: WorkflowContext):
    """Build node that validates Kite connectivity (lazy auth)."""

    async def authenticate_kite_node(state: WorkflowState) -> WorkflowState:
        ctx.progress("[1/6] Checking Kite connection...")
        next_state = init_next_state(state)
        next_state["kite_connected"] = ctx.mcp.kite_connected
        next_state["degraded_mode"] = not ctx.mcp.kite_connected
        next_state["halted"] = False

        if not ctx.mcp.kite_connected:
            next_state["auth_status"] = "kite_unavailable"
            if ctx.mcp.kite_error:
                append_error(next_state, f"Kite unavailable: {ctx.mcp.kite_error}")
            return next_state

        # Lazy auth: mark connected, do not verify session yet.
        next_state["auth_status"] = "kite_connected"
        return next_state

    return authenticate_kite_node
