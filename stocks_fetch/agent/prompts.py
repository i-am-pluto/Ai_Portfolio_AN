"""Prompt loading and construction utilities for the portfolio workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from stocks_fetch.agent.state.schema import WorkflowState

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "system_portfolio_analyst.md"


def load_system_prompt() -> str:
    """Load the base system prompt from disk."""
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def _to_json(data: Any, max_chars: int = 12000) -> str:
    """Serialize data for prompt context with truncation safety."""
    text = json.dumps(data, indent=2, default=str, ensure_ascii=True)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 14] + "\n...<truncated>"


def _data_coverage_summary(state: WorkflowState) -> str:
    """Build a concise data coverage summary from data_status."""
    data_status = state.get("data_status", {})
    if not data_status:
        return "No per-symbol data collection status available."

    lines = []
    for symbol, statuses in data_status.items():
        ok = [k for k, v in statuses.items() if v == "ok"]
        failed = [k for k, v in statuses.items() if v == "failed"]
        unavailable = [k for k, v in statuses.items() if v == "unavailable"]
        parts = [f"{symbol}:"]
        if ok:
            parts.append(f"collected={','.join(ok)}")
        if failed:
            parts.append(f"failed={','.join(failed)}")
        if unavailable:
            parts.append(f"unavailable={','.join(unavailable)}")
        lines.append(" ".join(parts))
    return "\n".join(lines)


def get_portfolio_analysis_prompt(state: WorkflowState) -> str:
    """Create the main analysis prompt from workflow state."""
    return (
        "Analyze this portfolio context and generate high-signal insights.\n\n"
        f"User request:\n{state.get('user_request', 'No explicit request provided.')}\n\n"
        f"Auth status: {state.get('auth_status', 'unknown')}\n"
        f"Degraded mode: {state.get('degraded_mode', False)}\n\n"
        "Data coverage:\n"
        f"{_data_coverage_summary(state)}\n\n"
        "Holdings:\n"
        f"{_to_json(state.get('holdings', []), max_chars=4000)}\n\n"
        "Per-symbol analysis:\n"
        f"{_to_json(state.get('per_symbol_analysis', {}), max_chars=8000)}\n\n"
        "Peer comparison:\n"
        f"{_to_json(state.get('peer_comparison', []), max_chars=3000)}\n\n"
        "Correlation and covariance output:\n"
        f"{_to_json(state.get('correlation_data', {}), max_chars=4000)}\n\n"
        "Return actionable portfolio insights with explicit risk commentary."
    )


def get_executive_summary_prompt(state: WorkflowState, insights_text: str) -> str:
    """Create prompt for a concise executive summary."""
    return (
        "Create a short executive summary from this portfolio analysis.\n\n"
        "Constraints:\n"
        "- 4 bullet points maximum\n"
        "- mention one strength and one key risk\n"
        "- mention data limitations if any\n\n"
        f"Data coverage:\n{_data_coverage_summary(state)}\n\n"
        f"Full insights:\n{insights_text[:6000]}"
    )
