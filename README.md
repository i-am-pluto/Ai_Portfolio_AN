# AI Portfolio Analyzer - MCP Server

An **MCP (Model Context Protocol) server** for analyzing Indian stock portfolios with real-time data fetching, technical analysis, and market insights.

Built with **FastMCP**, **yfinance**, and **nselib** to provide comprehensive analysis of NSE (National Stock Exchange) listed companies.

---

## ✨ Features

- **Portfolio Management**: Load and analyze custom stock portfolios
- **Price History & Technical Analysis**: Get historical data, returns, volatility
- **Fundamentals & Metrics**: P/E ratios, market cap, dividend yields, debt-to-equity
- **Corporate Actions**: Dividend history, stock splits, bonus information
- **Market Information**: Latest news, market context, sector analysis

All tools work with **NSE symbols** (e.g., `RELIANCE`, `TCS`, `HDFCBANK`) — no manual ticker conversion needed.

---

## 🏗️ Architecture

```
stocks_fetch/
├── server.py              # FastMCP entry point
├── __main__.py           # Module runner
└── sources/              # Tool modules
    ├── portfolio.py      # Portfolio loading & analysis
    ├── price_history.py  # Price data & technical metrics
    ├── fundamentals.py   # P/E, market cap, debt ratios
    ├── corporate.py      # Dividend, splits, bonus data
    └── market_info.py    # News, sector data
```

**Key Files:**
- `pyproject.toml` — Dependencies and project config
- `.mcp.json` — Claude Code MCP server configuration
- `data/portfolio.csv` — Sample portfolio (customizable via `PORTFOLIO_CSV` env var)
- `stocks_fetch/utils/symbols.py` — NSE ↔ Yahoo ticker mapping

---

## 📋 Prerequisites

- **Python 3.11+**
- **uv** package manager (installed at `~/.local/bin`)
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Internet connection** (for yfinance data fetching)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /Users/parikshit/Documents/code/Ai_Portfolio_AN
uv sync
```

This installs all dependencies in the project's local virtual environment.

### 2. Run the MCP Locally

**Option A: Using uv directly**
```bash
uv run python -m stocks_fetch
```

**Option B: In the background**
```bash
~/.local/bin/uv run --project /Users/parikshit/Documents/code/Ai_Portfolio_AN python -m stocks_fetch &
```

### 3. Integrate with Claude Code

The MCP is already configured in `.mcp.json` for use with Claude Code:

```json
{
  "mcpServers": {
    "portfolio-analyzer": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--project", "/Users/parikshit/Documents/code/Ai_Portfolio_AN", "python", "-m", "stocks_fetch"],
      "env": {
        "PORTFOLIO_CSV": "/Users/parikshit/Documents/code/Ai_Portfolio_AN/data/portfolio.csv"
      }
    }
  }
}
```

Once configured, the MCP server will automatically start when you access portfolio tools in Claude Code.

---

## ⚙️ Configuration

### Portfolio CSV Format

The portfolio is loaded from `data/portfolio.csv` (or a path specified by `PORTFOLIO_CSV` env var):

```csv
symbol,exchange,quantity,avg_price,buy_date,sector,notes
RELIANCE,NSE,15,2430.50,2023-06-15,Energy,Core holding - oil-to-digital conglomerate
TCS,NSE,10,3250.00,2023-01-10,IT,IT bellwether
HDFCBANK,NSE,20,1580.75,2022-11-20,Banking,Largest private bank
```

**Columns:**
- `symbol` — NSE ticker (e.g., RELIANCE, TCS)
- `exchange` — NSE or BSE
- `quantity` — Units held
- `avg_price` — Average purchase price
- `buy_date` — Purchase date (YYYY-MM-DD)
- `sector` — Industry classification
- `notes` — Optional investment thesis

### Custom Portfolio Path

Set the environment variable:
```bash
export PORTFOLIO_CSV="/path/to/your/portfolio.csv"
uv run python -m stocks_fetch
```

Or in `.mcp.json`:
```json
"env": {
  "PORTFOLIO_CSV": "/path/to/your/portfolio.csv"
}
```

---

## 📊 Available Tools

### Portfolio Tools
- `get_portfolio()` — Load and display current portfolio
- `portfolio_summary()` — Total value, returns, allocation breakdown
- `portfolio_performance()` — Historical returns, sector performance

### Price & Technical Tools
- `get_price_history(symbol, days)` — Historical OHLCV data
- `get_returns(symbol, days)` — Period returns & annualized return
- `get_volatility(symbol, days)` — Historical volatility metrics
- `technical_analysis(symbol, days)` — Moving averages, RSI, MACD indicators

### Fundamentals Tools
- `get_fundamentals(symbol)` — P/E, market cap, dividend yield, ROE, ROA
- `get_debt_equity(symbol)` — Debt-to-equity ratio
- `get_margins(symbol)` — Profit margins and efficiency metrics

### Corporate Actions Tools
- `get_dividend_history(symbol)` — Dividend records and yields
- `get_stock_splits(symbol)` — Stock split history
- `get_corporate_actions(symbol)` — Comprehensive corporate actions

### Market Info Tools
- `get_news(symbol)` — Latest market news
- `get_market_context(symbol)` — 52-week highs/lows, market sentiment
- `sector_analysis(symbol)` — Sector performance and peer comparison

---

## 🧪 Testing

Run the test suite:
```bash
uv run pytest
```

Check individual tool functionality:
```bash
uv run python -m stocks_fetch  # Start the server
# In another terminal, test with curl or Claude Code
```

---

## 🔧 Development

### Adding New Tools

Each source module exports a `register(mcp)` function to avoid circular imports:

```python
# stocks_fetch/sources/example.py
from fastmcp import FastMCP

def register(mcp: FastMCP):
    @mcp.tool()
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
- **Bank stocks** (e.g., HDFCBANK) may return `None` for debt_to_equity
- **NSE ticker normalization**: Tools automatically convert NSE symbols to Yahoo Finance format (`.NS` suffix)
- **nselib version**: Max available version is 2.4.2 (gracefully fallbacks if unavailable)

---

## 📝 Example Usage

### In Claude Code

```
"Analyze my portfolio holdings. What are the top performers?"
→ Uses: get_portfolio(), get_returns(), portfolio_summary()

"What's the PE ratio of TCS and how does it compare to INFY?"
→ Uses: get_fundamentals(symbol) for both stocks

"Show me the dividend history for RELIANCE over the last 5 years"
→ Uses: get_dividend_history(symbol)

"What's the technical setup for ASIANPAINT? Any buy signals?"
→ Uses: technical_analysis(symbol, days=90)
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| `uv: command not found` | Ensure `~/.local/bin` is in PATH: `export PATH="$PATH:~/.local/bin"` |
| MCP won't start | Check `.mcp.json` paths are correct and portfolio.csv exists |
| yfinance timeouts | Verify internet connection; some APIs have rate limits |
| No dividend data | Some stocks may not have dividend history on yfinance |
| HDFCBANK returns `None` for D/E | Bank stocks calculate debt differently; fallback to other metrics |

---

## 📚 Resources

- [FastMCP Documentation](https://mcp.run/)
- [yfinance GitHub](https://github.com/ranaroussi/yfinance)
- [NSE India](https://www.nseindia.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

## 📄 License

MIT

---

## 🤝 Contributing

To add new tools or improve existing ones:

1. Create/modify a source module in `stocks_fetch/sources/`
2. Export a `register(mcp)` function
3. Register in `stocks_fetch/server.py`
4. Test with `uv run pytest`
5. Update this README with new tool descriptions

