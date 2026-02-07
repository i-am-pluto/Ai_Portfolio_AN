# AI Portfolio Analyzer - Claude Code Configuration

## Project Context
- **Type**: MCP Server (FastMCP) - Indian stock portfolio analyzer
- **Tech Stack**: Python with yfinance, nselib, pandas, fastmcp
- **Entry Point**: `stocks_fetch/server.py`
- **Package Manager**: `uv` (installed at `~/.local/bin`)

## Architecture Overview
- `stocks_fetch/sources/` — 5 modules with 13 tools across:
  - Portfolio management
  - Price history & technical analysis
  - Fundamentals & metrics
  - Corporate actions
  - Market information & news
- `stocks_fetch/utils/symbols.py` — NSE ↔ Yahoo ticker mapping
- `data/portfolio.csv` — Sample 8-stock portfolio

## Key Development Notes
- Each source module exports `register(mcp)` to avoid circular imports
- yfinance news API returns nested structure: `[{id, content: {title, provider, ...}}]`
- Bank stocks (e.g., HDFCBANK) may return `None` for debt_to_equity
- nselib max version: 2.4.2

## Special Instructions

### Notion Documentation
✅ **Project created**: [AI Portfolio Analyzer - MCP Server](https://www.notion.so/300e9e4941268109931ed8f77fd5faf6)

**Guidelines**:
- Add a page for every major architectural/design update
- Skip minor fixes and code changes (self-documenting)
- Document deployment changes, module restructures, and integration updates
- Keep Notion in sync with project evolution


### Sound Feedback
**Play a short beep sound at the end of each task and whenever user input is required.**

Use this command to emit a beep:
```bash
afplay notification.mp3
```

This produces a terminal bell without any external dependencies (no mp3, no audio files).

**Implementation**: Add this to the end of task output or before prompting for input.

## Workflow Preferences
- Use `uv` for all Python operations
- Consult memory files for recurring issues
- Keep solutions focused and minimal
- Run tests after significant changes
