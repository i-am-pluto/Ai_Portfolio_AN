"""LangGraph assembly for the portfolio analysis workflow."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from langgraph.graph import END, START, StateGraph

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.mcp_client import AgentMCPClient
from stocks_fetch.agent.models.factory import build_model_gateway
from stocks_fetch.agent.state.schema import WorkflowState
from stocks_fetch.agent.workflow.context import WorkflowContext
from stocks_fetch.agent.workflow.helpers.state_updates import (
    init_next_state,
    mark_node_completed,
    mark_node_started,
)
from stocks_fetch.agent.workflow.nodes import (
    build_authenticate_kite_node,
    build_discover_tools_node,
    build_fetch_portfolio_context_node,
    build_gather_analysis_data_node,
    build_generate_insights_node,
    build_write_report_node,
)
from stocks_fetch.agent.workflow.routing import route_after_fetch


def _noop_progress(_: str) -> None:
    return None


def _wrap_node(
    node_name: str,
    node_fn: Callable[[WorkflowState], Awaitable[WorkflowState]],
) -> Callable[[WorkflowState], Awaitable[WorkflowState]]:
    async def _wrapped(state: WorkflowState) -> WorkflowState:
        next_state = init_next_state(state)
        mark_node_started(next_state, node_name)
        result = await node_fn(next_state)
        final_state = init_next_state(result)
        mark_node_completed(final_state, node_name)
        return final_state

    return _wrapped


def create_analysis_workflow(
    config: AgentConfig,
    mcp: AgentMCPClient,
    llm_factory: Callable[[AgentConfig], Any] | None = None,
    on_progress: Callable[[str], None] | None = None,
):
    """Create the portfolio analysis workflow using LangGraph."""
    progress = on_progress if on_progress is not None else _noop_progress
    context = WorkflowContext(
        config=config,
        mcp=mcp,
        progress=progress,
        model_gateway=build_model_gateway(config=config, llm_factory=llm_factory),
    )

    workflow = StateGraph(WorkflowState)

    authenticate_kite_node = build_authenticate_kite_node(context)
    discover_tools_node = build_discover_tools_node(context)
    fetch_portfolio_context_node = build_fetch_portfolio_context_node(context)
    gather_analysis_data_node = build_gather_analysis_data_node(context)
    generate_insights_node = build_generate_insights_node(context)
    write_report_node = build_write_report_node(context)

    workflow.add_node("authenticate_kite", _wrap_node("authenticate_kite", authenticate_kite_node))
    workflow.add_node("discover_tools", _wrap_node("discover_tools", discover_tools_node))
    workflow.add_node(
        "fetch_portfolio_context",
        _wrap_node("fetch_portfolio_context", fetch_portfolio_context_node),
    )
    workflow.add_node(
        "gather_analysis_data",
        _wrap_node("gather_analysis_data", gather_analysis_data_node),
    )
    workflow.add_node("generate_insights", _wrap_node("generate_insights", generate_insights_node))
    workflow.add_node("write_report", _wrap_node("write_report", write_report_node))

    workflow.add_edge(START, "authenticate_kite")
    workflow.add_edge("authenticate_kite", "discover_tools")
    workflow.add_edge("discover_tools", "fetch_portfolio_context")
    workflow.add_conditional_edges(
        "fetch_portfolio_context",
        route_after_fetch,
        {"stop": END, "continue": "gather_analysis_data"},
    )
    workflow.add_edge("gather_analysis_data", "generate_insights")
    workflow.add_edge("generate_insights", "write_report")
    workflow.add_edge("write_report", END)

    return workflow.compile()
