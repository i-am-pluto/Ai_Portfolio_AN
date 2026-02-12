# AI Stock Analyzer + Dual-MCP Portfolio Agent

This repository contains:
- A **FastMCP stock-analyzer server** for Indian equities
- A **LangGraph portfolio agent** that connects to both `kite` and `stock-analyzer`

The agent is login-first, strict read-only on Kite, and writes dated markdown reports.

## Architecture

```text
.mcp.json
stocks_fetch/
├── server.py                      # FastMCP stock-analyzer server
├── sources/
│   ├── fundamentals.py
│   ├── corporate.py
│   ├── market_info.py
│   └── technical.py               # correlation/covariance MCP tool
├── services/
│   ├── fundamentals.py
│   ├── corporate.py
│   ├── news.py
│   └── technical.py               # correlation/covariance computation
└── agent/
    ├── config.py
    ├── mcp_client.py
    ├── models/
    │   ├── factory.py
    │   ├── registry.py
    │   └── providers/
    │       ├── groq.py
    │       └── xai.py
    ├── state/
    │   ├── schema.py
    │   └── defaults.py
    ├── tool_filter.py
    ├── workflow/
    │   ├── graph.py               # graph assembly only
    │   ├── routing.py
    │   ├── errors.py
    │   ├── helpers/
    │   └── nodes/                 # one file per node
    ├── report_generator.py
    ├── runner.py                  # portfolio-report CLI
    └── prompts/system_portfolio_analyst.md
```

## Dual MCP Setup

| Server | Purpose |
| --- | --- |
| `kite` | Portfolio/account context, read-only market/account tools, login |
| `stock-analyzer` | Fundamentals, corporate actions, news, correlation/covariance |

## Quick Start

1. Install dependencies:
```bash
uv sync
```

2. Create local environment file:
```bash
cp .env.example .env
```

3. Edit `.env` and set your API key:
- For Grok (xAI): set `LLM_PROVIDER=grok` and fill `GROK_API_KEY`
- For Groq: set `LLM_PROVIDER=groq` and fill `GROQ_API_KEY`

4. Run stock-analyzer MCP server:
```bash
uv run python -m stocks_fetch
```

5. Run portfolio agent (auto-analysis + conversational mode):
```bash
uv run portfolio-report
```
If Kite authentication is needed, the CLI will print a login URL, wait for you to complete browser login, and then continue analysis in the same session.

6. Run one-shot mode:
```bash
uv run portfolio-report --one-shot
```

## Environment Variables

- `LLM_PROVIDER` (optional, default: `groq`; options: `groq`, `grok`, `xai`)
- `GROK_API_KEY` or `XAI_API_KEY` (required when `LLM_PROVIDER=grok`/`xai`)
- `GROK_MODEL` or `XAI_MODEL` (optional, default: `grok-2-latest`)
- `XAI_BASE_URL` (optional, default: `https://api.x.ai/v1`)
- `GROQ_API_KEY` (required when `LLM_PROVIDER=groq`)
- `GROQ_MODEL` (optional, default: `llama-3.3-70b-versatile`)
- `USE_KITE` (optional, default: `true`)
- `KITE_SSE_URL` (optional, default: `https://mcp.kite.trade/sse`)
- `CORRELATION_PERIOD` (optional, default: `1y`)
- `CORRELATION_INTERVAL` (optional, default: `1d`)
- `CORRELATION_RETURNS_TYPE` (optional, default: `simple`)
- `PORTFOLIO_REPORT_DIR` (optional, default: `reports`)

## Stock Analyzer Tools (7)

- `get_fundamental_ratios(symbol)`
- `get_financial_statements(symbol, statement, quarterly)`
- `get_peer_comparison(symbols)`
- `get_dividends_and_splits(symbol)`
- `get_nse_corporate_actions(symbol, period)`
- `get_stock_news(symbol, count)`
- `get_stock_correlations(symbols, period, interval, returns_type, annualize_covariance)`

## Safety Policy

Kite is strict allowlist only:
- login + read-only portfolio/account/market data tools
- hard block for risky keywords: `buy`, `sell`, `place`, `modify`, `cancel`, `basket`, `gtt`, `exit`, `squareoff`, `convert`

No order/trade mutation tools are executed by the agent.

## Report Output

Reports are written as:
- `reports/portfolio_analysis_YYYY-MM-DD.md`

Each report includes:
- auth + tool status
- holdings snapshot
- per-symbol fundamentals/news/corporate notes
- correlation matrix
- covariance matrix
- executive summary and detailed insights
- warnings/errors
