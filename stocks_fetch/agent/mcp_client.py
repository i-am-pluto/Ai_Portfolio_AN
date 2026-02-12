"""MCP client abstraction for Kite and stock-analyzer servers."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from fastmcp import Client

from stocks_fetch.agent.tool_filter import is_tool_allowed
from stocks_fetch.server import mcp as stock_mcp

logger = logging.getLogger(__name__)

# Minimum interval between consecutive Kite API calls (seconds)
_KITE_MIN_INTERVAL = 0.5


def _parse_tool_result(result: Any) -> Any:
    """Extract usable Python data from a FastMCP CallToolResult."""
    if result is None:
        return None

    data = getattr(result, "data", None)
    if data is not None:
        return data

    structured = getattr(result, "structured_content", None)
    if structured is not None:
        return structured

    content = getattr(result, "content", None) or []
    if not content:
        return None

    text_chunks: list[str] = []
    for chunk in content:
        text = getattr(chunk, "text", None)
        text_chunks.append(text if isinstance(text, str) else str(chunk))

    if len(text_chunks) == 1:
        try:
            return json.loads(text_chunks[0])
        except Exception:
            return text_chunks[0]

    for chunk in text_chunks:
        try:
            return json.loads(chunk)
        except Exception:
            continue

    joined = "\n".join(text_chunks)
    try:
        return json.loads(joined)
    except Exception:
        return joined


class AgentMCPClient:
    """Manages dual MCP connections and safety-enforced tool execution."""

    def __init__(self, kite_sse_url: str, use_kite: bool = True) -> None:
        self._kite_sse_url = kite_sse_url
        self._use_kite = use_kite
        self._stock_client: Client | None = None
        self._kite_client: Client | None = None
        self._tool_cache: dict[str, list[dict[str, Any]]] = {
            "stock-analyzer": [],
            "kite": [],
        }
        self._kite_error: str | None = None
        self._last_kite_call: float = 0.0

    @property
    def kite_connected(self) -> bool:
        """Return True if Kite client connection is active."""
        return self._kite_client is not None

    @property
    def kite_error(self) -> str | None:
        """Return last Kite connection error, if any."""
        return self._kite_error

    async def connect(self) -> None:
        """Connect to stock-analyzer and optionally Kite MCP."""
        logger.info("Connecting to stock-analyzer MCP (in-process)...")
        self._stock_client = Client(stock_mcp, name="stock-analyzer")
        await self._stock_client.__aenter__()
        logger.info("stock-analyzer connected.")

        if not self._use_kite:
            logger.info("Kite MCP disabled (USE_KITE=false).")
            return

        try:
            logger.info("Connecting to Kite MCP at %s...", self._kite_sse_url)
            self._kite_client = Client(self._kite_sse_url, name="kite")
            await self._kite_client.__aenter__()
            self._kite_error = None
            logger.info("Kite MCP connected.")
        except Exception as exc:
            self._kite_client = None
            self._kite_error = str(exc)
            logger.warning("Kite MCP connection failed: %s", exc)

    async def disconnect(self) -> None:
        """Disconnect active MCP clients."""
        if self._kite_client is not None:
            await self._kite_client.__aexit__(None, None, None)
            self._kite_client = None
        if self._stock_client is not None:
            await self._stock_client.__aexit__(None, None, None)
            self._stock_client = None

    async def __aenter__(self) -> AgentMCPClient:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # type: ignore[no-untyped-def]
        await self.disconnect()

    def _client_for(self, server: str) -> Client:
        if server == "stock-analyzer" and self._stock_client is not None:
            return self._stock_client
        if server == "kite" and self._kite_client is not None:
            return self._kite_client
        raise RuntimeError(f"{server} MCP server is not connected.")

    async def list_tools(self, server: str, refresh: bool = False) -> list[dict[str, Any]]:
        """List tool metadata from a server as normalized dictionaries."""
        if not refresh and self._tool_cache.get(server):
            return self._tool_cache[server]

        logger.info("Listing tools from %s (refresh=%s)...", server, refresh)
        client = self._client_for(server)
        tools = await client.list_tools()
        normalized = []
        for tool in tools:
            normalized.append(
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema or {},
                }
            )
        self._tool_cache[server] = normalized
        tool_names = [t["name"] for t in normalized]
        logger.info("  %s tools: %s", server, tool_names)
        return normalized

    async def find_tool_name(
        self,
        server: str,
        preferred_names: list[str] | None = None,
        fuzzy_keywords: list[str] | None = None,
        refresh: bool = False,
    ) -> str | None:
        """Find a server tool by preferred exact name or fuzzy keyword match."""
        preferred_names = preferred_names or []
        fuzzy_keywords = fuzzy_keywords or []
        tools = await self.list_tools(server, refresh=refresh)

        by_name = {tool["name"].lower(): tool["name"] for tool in tools}
        for preferred in preferred_names:
            found = by_name.get(preferred.lower())
            if found:
                return found

        for tool in tools:
            low_name = tool["name"].lower()
            if all(keyword.lower() in low_name for keyword in fuzzy_keywords):
                return tool["name"]
        return None

    async def _throttle_kite(self) -> None:
        """Rate-limit Kite API calls to avoid 429s."""
        elapsed = time.monotonic() - self._last_kite_call
        if elapsed < _KITE_MIN_INTERVAL:
            wait = _KITE_MIN_INTERVAL - elapsed
            logger.debug("Kite rate-limit: waiting %.2fs", wait)
            await asyncio.sleep(wait)
        self._last_kite_call = time.monotonic()

    async def call_tool(self, server: str, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Call a tool with centralized safety checks and parsed output."""
        if not is_tool_allowed(tool_name, server):
            raise ValueError(f"Tool '{tool_name}' is blocked by safety policy for {server}.")

        logger.info("Calling %s:%s(%s)", server, tool_name, arguments)

        if server == "kite":
            await self._throttle_kite()

        client = self._client_for(server)
        result = await client.call_tool(
            tool_name,
            arguments=arguments,
            raise_on_error=False,
        )

        if getattr(result, "is_error", False):
            parsed_error = str(_parse_tool_result(result))
            if len(parsed_error) > 300:
                parsed_error = parsed_error[:300] + "..."
            logger.warning("  %s:%s FAILED: %s", server, tool_name, parsed_error)
            raise RuntimeError(f"{server}:{tool_name} failed: {parsed_error}")

        logger.info("  %s:%s OK", server, tool_name)
        return _parse_tool_result(result)
