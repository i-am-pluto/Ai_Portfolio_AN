"""Write-report workflow node."""

from __future__ import annotations

from stocks_fetch.agent.report_generator import generate_report
from stocks_fetch.agent.state.schema import WorkflowState
from stocks_fetch.agent.workflow.context import WorkflowContext
from stocks_fetch.agent.workflow.errors import WorkflowError, append_error
from stocks_fetch.agent.workflow.helpers.state_updates import init_next_state


def build_write_report_node(ctx: WorkflowContext):
    """Build node that writes markdown report to disk."""

    async def write_report_node(state: WorkflowState) -> WorkflowState:
        ctx.progress("[6/6] Writing report...")
        next_state = init_next_state(state)
        try:
            next_state["report_path"] = generate_report(next_state, ctx.config.report_dir)
        except Exception as exc:
            append_error(next_state, f"Report generation failed: {exc}")
            raise WorkflowError(f"Failed to write report: {exc}") from exc
        return next_state

    return write_report_node
