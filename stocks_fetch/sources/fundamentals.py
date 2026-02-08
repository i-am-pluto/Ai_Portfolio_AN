"""Fundamental ratios, financial statements, and peer comparison tools."""

from typing import Literal

from stocks_fetch.services import fundamentals as fundamentals_service
from stocks_fetch.utils.symbols import validate_symbol


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
        err = validate_symbol(symbol)
        if err:
            return err

        return fundamentals_service.get_fundamental_ratios(symbol)

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
        err = validate_symbol(symbol)
        if err:
            return err

        return fundamentals_service.get_financial_statement(symbol, statement, quarterly)

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_peer_comparison(symbols: list[str]) -> list[dict] | str:
        """Compare fundamental metrics across multiple stocks side-by-side.

        Args:
            symbols: List of NSE stock symbols (e.g., ['TCS', 'INFY', 'WIPRO']).
                     Maximum 10 symbols.

        Returns list of dicts, one per stock, with: symbol, current_price, market_cap,
        pe, pb, roe, debt_to_equity, dividend_yield, revenue_growth, profit_margins.
        """
        return fundamentals_service.compare_peers(symbols)
