"""Gather-analysis-data workflow node."""

from __future__ import annotations

from stocks_fetch.agent.state.schema import WorkflowState
from stocks_fetch.agent.workflow.context import WorkflowContext
from stocks_fetch.agent.workflow.helpers.data_fetch import (
    collect_cross_symbol_metrics,
    collect_symbol_analysis,
    enrich_with_kite_secondary,
)
from stocks_fetch.agent.workflow.helpers.state_updates import init_next_state
from stocks_fetch.agent.workflow.helpers.tools import discovered_tool_names


def build_gather_analysis_data_node(ctx: WorkflowContext):
    """Build node that collects per-symbol and portfolio-level analytics."""

    async def gather_analysis_data_node(state: WorkflowState) -> WorkflowState:
        next_state = init_next_state(state)
        symbols = list(next_state.get("symbols", []))
        per_symbol: dict[str, dict[str, object]] = {}
        data_status: dict[str, dict[str, str]] = {}

        discovered_sa = discovered_tool_names(next_state, "stock-analyzer")
        retry_delay = ctx.config.tool_retry_delay

        total = len(symbols)
        for idx, symbol in enumerate(symbols, 1):
            ctx.progress(f"[4/6] Analyzing {symbol} ({idx}/{total})...")
            details, sym_status = await collect_symbol_analysis(
                mcp=ctx.mcp,
                state=next_state,
                symbol=symbol,
                discovered_sa=discovered_sa,
                retry_delay=retry_delay,
            )
            per_symbol[symbol] = details
            data_status[symbol] = sym_status

        next_state["per_symbol_analysis"] = per_symbol
        next_state["data_status"] = data_status

        await collect_cross_symbol_metrics(
            mcp=ctx.mcp,
            state=next_state,
            symbols=symbols,
            discovered_sa=discovered_sa,
            config=ctx.config,
            retry_delay=retry_delay,
        )

        if ctx.mcp.kite_connected:
            kite_tools = next_state.get("tools_catalog", {}).get("kite", [])
            await enrich_with_kite_secondary(
                mcp=ctx.mcp,
                per_symbol=per_symbol,
                symbols=symbols,
                kite_tools=kite_tools,
            )

        return next_state

    return gather_analysis_data_node
