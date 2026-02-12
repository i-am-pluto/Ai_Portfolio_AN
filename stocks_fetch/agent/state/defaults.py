"""State initialization helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from stocks_fetch.agent.state.schema import WorkflowState


_DEFAULT_USER_REQUEST = "Run full portfolio analysis using all available fundamentals."


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat()


def build_initial_state(user_request: str | None = None) -> WorkflowState:
    """Create a fresh workflow state for each run cycle."""
    now = _utc_now_iso()
    return WorkflowState(
        run_id=str(uuid4()),
        started_at=now,
        updated_at=now,
        current_node="",
        completed_nodes=[],
        user_request=user_request or _DEFAULT_USER_REQUEST,
        auth_status="pending",
        kite_connected=False,
        degraded_mode=False,
        halted=False,
        tools_catalog={},
        holdings=[],
        symbols=[],
        per_symbol_analysis={},
        peer_comparison=[],
        correlation_data={},
        data_status={},
        portfolio_insights="",
        executive_summary="",
        report_path="",
        errors=[],
    )
