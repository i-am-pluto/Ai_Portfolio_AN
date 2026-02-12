"""Tool-discovery and tool-argument helper utilities."""

from __future__ import annotations

from typing import Any

from stocks_fetch.agent.mcp_client import AgentMCPClient
from stocks_fetch.agent.state.schema import ToolSpec, WorkflowState
from stocks_fetch.agent.workflow.errors import append_error


def as_list_records(payload: Any) -> list[dict[str, Any]]:
    """Normalize heterogeneous tool results into a list of records."""
    if payload is None:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("data", "holdings", "positions", "net", "day", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [payload]
    return []


def tool_summary(tool: dict[str, Any]) -> ToolSpec:
    return ToolSpec(
        name=str(tool.get("name", "")),
        description=str(tool.get("description", "")),
        input_schema=tool.get("input_schema", {}),
    )


def discovered_tool_names(state: WorkflowState, server: str) -> set[str]:
    tools = state.get("tools_catalog", {}).get(server, [])
    return {tool["name"] for tool in tools if isinstance(tool, dict)}


async def discover_server_tools(
    mcp: AgentMCPClient,
    server: str,
    state: WorkflowState,
) -> list[ToolSpec]:
    """Discover tools from a server and normalize metadata."""
    try:
        tools = await mcp.list_tools(server, refresh=True)
        return [tool_summary(tool) for tool in tools]
    except Exception as exc:
        server_label = "Kite" if server == "kite" else server
        append_error(state, f"Failed to list {server_label} tools: {exc}")
        return []


def build_kite_symbol_args(input_schema: dict[str, Any], symbol: str) -> dict[str, Any] | None:
    """Build best-effort arguments for read-only Kite market data tools."""
    properties = input_schema.get("properties", {}) if isinstance(input_schema, dict) else {}
    required = input_schema.get("required", []) if isinstance(input_schema, dict) else []

    args: dict[str, Any] = {}
    for key in properties:
        lowered = key.lower()
        if lowered in {"symbol", "tradingsymbol"}:
            args[key] = symbol
        elif lowered == "exchange":
            args[key] = "NSE"
        elif lowered in {"instrument", "instrument_token"}:
            args[key] = f"NSE:{symbol}"
        elif lowered in {"instruments", "tradingsymbols", "symbols"}:
            args[key] = [f"NSE:{symbol}"]

    for req in required:
        if req not in args:
            return None
    return args
