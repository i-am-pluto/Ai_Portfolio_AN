"""Kite auth and portfolio-context helper utilities."""

from __future__ import annotations

import re
from typing import Any

from stocks_fetch.agent.mcp_client import AgentMCPClient
from stocks_fetch.agent.state.schema import ToolSpec, WorkflowState
from stocks_fetch.agent.workflow.errors import _is_auth_error, append_error
from stocks_fetch.agent.workflow.helpers.state_updates import reset_kite_context
from stocks_fetch.agent.workflow.helpers.tools import as_list_records


async def resolve_kite_login_tool(mcp: AgentMCPClient) -> str | None:
    """Resolve Kite login tool with a refresh fallback for first-run races."""
    login_tool = await mcp.find_tool_name(
        "kite",
        preferred_names=["login"],
        fuzzy_keywords=["login"],
    )
    if login_tool:
        return login_tool

    return await mcp.find_tool_name(
        "kite",
        preferred_names=["login"],
        fuzzy_keywords=["login"],
        refresh=True,
    )


def extract_login_url(payload: Any) -> str:
    """Extract the most likely login URL from tool payload."""
    url_pattern = re.compile(r"https?://[^\s<>'\"`]+")

    def _clean(url: str) -> str:
        cleaned = url.strip()
        while cleaned and cleaned[-1] in ".,;:)]}>":
            cleaned = cleaned[:-1]
        return cleaned

    def _find_in_str(text: str) -> str:
        match = url_pattern.search(text)
        if not match:
            return ""
        return _clean(match.group(0))

    def _walk(value: Any) -> str:
        if isinstance(value, str):
            return _find_in_str(value)

        if isinstance(value, dict):
            for key in ("login_url", "url", "auth_url", "redirect_url", "message", "text"):
                candidate = value.get(key)
                found = _walk(candidate)
                if found:
                    return found
            for candidate in value.values():
                found = _walk(candidate)
                if found:
                    return found
            return ""

        if isinstance(value, list | tuple | set):
            for candidate in value:
                found = _walk(candidate)
                if found:
                    return found
            return ""

        return _find_in_str(str(value))

    return _walk(payload)


def find_kite_portfolio_tools(tools: list[ToolSpec]) -> list[str]:
    """Resolve candidate Kite tools that may return holdings or positions."""
    tool_names = [tool["name"] for tool in tools if isinstance(tool, dict) and tool.get("name")]
    candidates: list[str] = []

    for preferred in ("get_holdings", "holdings", "get_positions", "positions"):
        if preferred in tool_names:
            candidates.append(preferred)

    for name in tool_names:
        lowered = name.lower()
        if ("holding" in lowered or "position" in lowered) and name not in candidates:
            candidates.append(name)

    return candidates


async def fetch_kite_holdings(
    mcp: AgentMCPClient,
    state: WorkflowState,
    candidate_tools: list[str],
) -> tuple[list[dict[str, Any]], bool]:
    """Fetch holdings records from candidate Kite tools.

    Returns `(records, auth_failure)` where `auth_failure` indicates the fetch
    should transition to login flow.
    """
    holdings: list[dict[str, Any]] = []

    for tool_name in candidate_tools:
        try:
            data = await mcp.call_tool("kite", tool_name, {})
        except Exception as exc:
            if _is_auth_error(exc):
                return holdings, True
            append_error(state, f"Kite {tool_name} failed: {exc}")
            continue

        records = as_list_records(data)
        if records:
            holdings.extend(records)

    return holdings, False


async def transition_to_kite_login(
    state: WorkflowState,
    mcp: AgentMCPClient,
) -> WorkflowState:
    """Trigger Kite login and update workflow state for manual continuation."""
    login_tool = await resolve_kite_login_tool(mcp)
    if not login_tool:
        state["auth_status"] = "kite_missing_login_tool"
        state["halted"] = True
        append_error(state, "Kite connected but no login tool was discovered.")
        reset_kite_context(state)
        return state

    try:
        login_result = await mcp.call_tool("kite", login_tool, {})
        state["kite_login_result"] = login_result
    except Exception as exc:
        state["auth_status"] = "kite_login_failed"
        state["halted"] = True
        append_error(state, f"Kite login failed: {exc}")
        reset_kite_context(state)
        return state

    login_url = extract_login_url(login_result)
    if login_url:
        state["kite_login_url"] = login_url
        state["auth_status"] = "kite_login_required"
        state["halted"] = True
    else:
        state["auth_status"] = "kite_login_pending"
        state["halted"] = True
        append_error(
            state,
            "Kite login was initiated but session is not authenticated yet. "
            "Complete login in browser and resume.",
        )

    reset_kite_context(state)
    return state
