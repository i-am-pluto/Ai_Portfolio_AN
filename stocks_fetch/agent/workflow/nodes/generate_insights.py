"""Generate-insights workflow node."""

from __future__ import annotations

from stocks_fetch.agent.prompts import (
    get_executive_summary_prompt,
    get_portfolio_analysis_prompt,
    load_system_prompt,
)
from stocks_fetch.agent.state.schema import WorkflowState
from stocks_fetch.agent.workflow.context import WorkflowContext
from stocks_fetch.agent.workflow.errors import append_error
from stocks_fetch.agent.workflow.helpers.data_fetch import fallback_insights
from stocks_fetch.agent.workflow.helpers.state_updates import init_next_state


def build_generate_insights_node(ctx: WorkflowContext):
    """Build node that generates detailed insights and executive summary."""

    async def generate_insights_node(state: WorkflowState) -> WorkflowState:
        ctx.progress("[5/6] Generating LLM insights...")
        next_state = init_next_state(state)

        system_prompt = load_system_prompt()
        user_prompt = get_portfolio_analysis_prompt(next_state)

        try:
            insights = ctx.model_gateway.invoke_text(system_prompt, user_prompt)
            next_state["portfolio_insights"] = insights

            summary_prompt = get_executive_summary_prompt(next_state, insights)
            next_state["executive_summary"] = ctx.model_gateway.invoke_text(
                system_prompt,
                summary_prompt,
            )
        except Exception as exc:
            append_error(next_state, f"LLM insight generation failed: {exc}")
            next_state["portfolio_insights"] = fallback_insights(next_state)
            next_state["executive_summary"] = (
                "Automated LLM summary unavailable. Using deterministic fallback insights."
            )

        return next_state

    return generate_insights_node
