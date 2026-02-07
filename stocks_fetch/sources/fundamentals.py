"""Fundamental ratios, financial statements, and peer comparison tools."""

import time
from typing import Literal

import yfinance as yf

from stocks_fetch.utils.symbols import to_yahoo_symbol


def register(mcp) -> None:
    """Register fundamentals tools on the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_fundamental_ratios(symbol: str) -> dict | str:
        """Get key fundamental ratios for long-term investment analysis.

        Args:
            symbol: NSE stock symbol (e.g., 'RELIANCE'). Do not include .NS suffix.

        Returns dict with sections:
        - valuation: PE, forward_PE, PB, dividend_yield, market_cap
        - profitability: ROE, ROA, profit_margins, operating_margins, gross_margins
        - leverage: debt_to_equity, current_ratio, quick_ratio
        - growth: revenue_growth, earnings_growth
        - cash: operating_cashflow, free_cashflow
        - meta: sector, industry, employees, summary (truncated to 500 chars)
        """
        ticker = yf.Ticker(to_yahoo_symbol(symbol))
        info = ticker.info

        if not info or not info.get("symbol"):
            return f"No data found for {symbol}. Check if the symbol is valid."

        summary = info.get("longBusinessSummary", "")
        if len(summary) > 500:
            summary = summary[:497] + "..."

        return {
            "symbol": symbol.upper(),
            "valuation": {
                "pe_trailing": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "pb": info.get("priceToBook"),
                "dividend_yield": info.get("dividendYield"),
                "market_cap": info.get("marketCap"),
            },
            "profitability": {
                "roe": info.get("returnOnEquity"),
                "roa": info.get("returnOnAssets"),
                "profit_margins": info.get("profitMargins"),
                "operating_margins": info.get("operatingMargins"),
                "gross_margins": info.get("grossMargins"),
            },
            "leverage": {
                "debt_to_equity": info.get("debtToEquity"),
                "current_ratio": info.get("currentRatio"),
                "quick_ratio": info.get("quickRatio"),
            },
            "growth": {
                "revenue_growth": info.get("revenueGrowth"),
                "earnings_growth": info.get("earningsGrowth"),
            },
            "cash": {
                "operating_cashflow": info.get("operatingCashflow"),
                "free_cashflow": info.get("freeCashflow"),
            },
            "meta": {
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "employees": info.get("fullTimeEmployees"),
                "summary": summary,
            },
        }

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_financial_statements(
        symbol: str,
        statement: Literal["income", "balance_sheet", "cashflow"] = "income",
        quarterly: bool = False,
    ) -> list[dict] | str:
        """Get financial statements for an Indian stock.

        Args:
            symbol: NSE stock symbol (e.g., 'RELIANCE'). Do not include .NS suffix.
            statement: Type of statement — 'income', 'balance_sheet', or 'cashflow'.
            quarterly: If True, returns quarterly data; otherwise annual.

        Returns list of dicts, one per fiscal period (most recent first).
        Each dict has a 'period' key (date string) and line items as keys with values in INR.
        """
        ticker = yf.Ticker(to_yahoo_symbol(symbol))

        stmt_map = {
            "income": (ticker.income_stmt, ticker.quarterly_income_stmt),
            "balance_sheet": (ticker.balance_sheet, ticker.quarterly_balance_sheet),
            "cashflow": (ticker.cashflow, ticker.quarterly_cashflow),
        }

        annual_stmt, quarterly_stmt = stmt_map[statement]
        df = quarterly_stmt if quarterly else annual_stmt

        if df is None or df.empty:
            return f"No {statement} data found for {symbol}."

        # yfinance returns line items as rows, periods as columns
        # Transpose so each period becomes a row
        records = []
        for col in df.columns:
            period_data = {"period": col.strftime("%Y-%m-%d")}
            for item, value in df[col].items():
                # Convert numpy types to Python native
                if value is not None and str(value) != "nan":
                    period_data[str(item)] = float(value)
                else:
                    period_data[str(item)] = None
            records.append(period_data)

        return records

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_peer_comparison(symbols: list[str]) -> list[dict] | str:
        """Compare fundamental metrics across multiple stocks side-by-side.

        Args:
            symbols: List of NSE stock symbols (e.g., ['TCS', 'INFY', 'WIPRO']).
                     Maximum 10 symbols.

        Returns list of dicts, one per stock, with: symbol, current_price, market_cap,
        pe, pb, roe, debt_to_equity, dividend_yield, revenue_growth, profit_margins.
        """
        if len(symbols) > 10:
            return "Maximum 10 symbols allowed for comparison."

        results = []
        for i, sym in enumerate(symbols):
            ticker = yf.Ticker(to_yahoo_symbol(sym))
            info = ticker.info

            results.append({
                "symbol": sym.upper(),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "market_cap": info.get("marketCap"),
                "pe": info.get("trailingPE"),
                "pb": info.get("priceToBook"),
                "roe": info.get("returnOnEquity"),
                "debt_to_equity": info.get("debtToEquity"),
                "dividend_yield": info.get("dividendYield"),
                "revenue_growth": info.get("revenueGrowth"),
                "profit_margins": info.get("profitMargins"),
            })

            # Rate limit: pause between calls (skip after last)
            if i < len(symbols) - 1:
                time.sleep(0.5)

        return results
