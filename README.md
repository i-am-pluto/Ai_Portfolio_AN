# AI Stock Analyzer - MCP Server

An **MCP (Model Context Protocol) server** providing analytical tools for Indian stocks — fundamentals, corporate actions, and news. Designed to work alongside **Zerodha Kite MCP** which handles portfolio data, real-time prices, and trading.

Built with **FastMCP**, **yfinance**, and **nselib**.

---

## Architecture

```
.mcp.json                  # Dual-server config (Kite MCP + stock-analyzer)
stocks_fetch/
├── server.py              # FastMCP entry point (3 modules)
├── __main__.py            # Module runner
├── sources/
│   ├── fundamentals.py    # PE, PB, ROE, financial statements, peer comparison
│   ├── corporate.py       # Dividends, splits, NSE corporate actions
│   └── market_info.py     # Stock news
└── utils/
    └── symbols.py         # NSE → Yahoo ticker mapping
```

### Dual MCP Setup

| Server | Handles | Source |
|--------|---------|--------|
| **Kite MCP** (Zerodha) | Portfolio holdings, real-time prices, historical data, order management | `https://mcp.kite.trade/sse` |
| **Stock Analyzer** (this) | Fundamentals, financial statements, corporate actions, news | Local FastMCP server |

---

## Prerequisites

- **Python 3.11+**
- **uv** package manager — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Node.js** — required for Kite MCP via `npx mcp-remote`
- **Zerodha account** — for Kite MCP authentication
- **Internet connection**

---

## Quick Start

### 1. Install Dependencies

```bash
cd /Users/parikshit/Documents/code/Ai_Portfolio_AN
uv sync
```

### 2. Run the MCP Server

```bash
uv run python -m stocks_fetch
```

### 3. Claude Code Integration

The `.mcp.json` configures both servers:

```json
{
  "mcpServers": {
    "kite": {
      "command": "npx",
      "args": ["mcp-remote", "https://mcp.kite.trade/sse"]
    },
    "stock-analyzer": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--project", "~/Documents/code/Ai_Portfolio_AN", "python", "-m", "stocks_fetch"]
    }
  }
}
```

Kite MCP authenticates via browser-based Zerodha 2FA — credentials never pass through the AI.

---

## Available Tools (6)

### Fundamentals (3 tools)
- `get_fundamental_ratios(symbol)` — PE, PB, ROE, margins, leverage, growth metrics
- `get_financial_statements(symbol, statement, quarterly)` — Income, balance sheet, or cashflow
- `get_peer_comparison(symbols)` — Side-by-side comparison of up to 10 stocks

### Corporate Actions (2 tools)
- `get_dividends_and_splits(symbol)` — Dividend and stock split history
- `get_nse_corporate_actions(symbol)` — Recent/upcoming NSE corporate actions

### News (1 tool)
- `get_stock_news(symbol, count)` — Recent news articles from Yahoo Finance

All tools accept **NSE symbols** (e.g., `RELIANCE`, `TCS`) — no `.NS` suffix needed.

---

## Development

### Adding New Tools

Each source module exports a `register(mcp)` function:

```python
# stocks_fetch/sources/example.py
def register(mcp) -> None:
    @mcp.tool(annotations={"readOnlyHint": True})
    def my_tool(param: str) -> str:
        """Description of what the tool does."""
        return f"Result for {param}"
```

Then register in `server.py`:
```python
from stocks_fetch.sources.example import register as register_example
register_example(mcp)
```

### Key Gotchas

- **yfinance news API** returns nested structure: `[{id, content: {title, provider, ...}}]`
- **Bank stocks** (e.g., HDFCBANK) may return `None` for `debt_to_equity`
- **nselib** max available version is 2.4.2 (graceful fallback if unavailable)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `uv: command not found` | Ensure `~/.local/bin` is in PATH |
| `npx: command not found` | Install Node.js from nodejs.org |
| Kite MCP auth fails | Re-authenticate via browser; session may have expired |
| yfinance timeouts | Check internet connection; APIs may have rate limits |
| HDFCBANK returns `None` for D/E | Bank stocks calculate debt differently |

---

## Resources

- [Kite MCP - Zerodha](https://zerodha.com/z-connect/featured/connect-your-zerodha-account-to-ai-assistants-with-kite-mcp)
- [FastMCP Documentation](https://mcp.run/)
- [yfinance GitHub](https://github.com/ranaroussi/yfinance)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

## License

MIT
