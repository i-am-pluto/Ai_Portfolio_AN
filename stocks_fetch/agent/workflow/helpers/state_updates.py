"""State mutation helpers shared across workflow nodes and graph wrappers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from stocks_fetch.agent.state.schema import WorkflowState


def utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def init_next_state(state: WorkflowState) -> WorkflowState:
    """Clone state and ensure common mutable collections exist."""
    next_state = dict(state)
    next_state.setdefault("errors", [])
    next_state.setdefault("completed_nodes", [])
    return next_state


def reset_kite_context(state: WorkflowState) -> None:
    """Clear holdings/symbols when login is pending or unavailable."""
    state["holdings"] = []
    state["symbols"] = []


def mark_node_started(state: WorkflowState, node_name: str) -> None:
    if not state.get("run_id"):
        state["run_id"] = str(uuid4())
    if not state.get("started_at"):
        state["started_at"] = utc_now_iso()
    state["current_node"] = node_name
    state["updated_at"] = utc_now_iso()


def mark_node_completed(state: WorkflowState, node_name: str) -> None:
    completed = list(state.get("completed_nodes", []))
    if node_name not in completed:
        completed.append(node_name)
    state["completed_nodes"] = completed
    state["updated_at"] = utc_now_iso()
