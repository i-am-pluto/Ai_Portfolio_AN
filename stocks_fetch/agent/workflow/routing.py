"""Workflow routing helpers."""

from __future__ import annotations

from stocks_fetch.agent.state.schema import WorkflowState


def route_after_fetch(state: WorkflowState) -> str:
    """Stop graph when fetch node requests manual intervention."""
    return "stop" if state.get("halted") else "continue"
