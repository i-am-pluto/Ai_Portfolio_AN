"""Corporate actions, dividends, and splits tools."""

from typing import Literal

from stocks_fetch.services import corporate as corporate_service
from stocks_fetch.utils.symbols import validate_symbol


def register(mcp) -> None:
    """Register corporate action tools on the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_dividends_and_splits(symbol: str) -> dict | str:
        """Get dividend and stock split history for an Indian stock.

        Args:
            symbol: NSE stock symbol (e.g., 'ITC'). Do not include .NS suffix.

        Returns dict with:
        - dividends: list of {date, amount} sorted most recent first
        - splits: list of {date, ratio} sorted most recent first
        """
        err = validate_symbol(symbol)
        if err:
            return err

        return corporate_service.get_dividends_and_splits(symbol)

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_nse_corporate_actions(
        symbol: str | None = None,
        period: Literal["1D", "1W", "1M", "6M", "1Y"] = "1M",
    ) -> list[dict] | str:
        """Get recent and upcoming corporate actions from NSE (dividends, splits, bonuses).

        Args:
            symbol: Optional NSE stock symbol to filter by. If None, returns recent actions
                    across all stocks.
            period: Time period to look back — '1D', '1W', '1M', '6M', or '1Y'. Default '1M'.

        Returns list of dicts with corporate action details.
        Note: This uses the nselib library which depends on NSE website availability.
        If NSE endpoints are down, returns an error message.
        """
        return corporate_service.get_nse_corporate_actions(symbol, period)
