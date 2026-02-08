"""Stock news tools."""

from stocks_fetch.constants import MAX_NEWS_COUNT
from stocks_fetch.services import news as news_service
from stocks_fetch.utils.symbols import validate_symbol


def register(mcp) -> None:
    """Register market info tools on the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_stock_news(symbol: str, count: int = 5) -> list[dict] | str:
        """Get recent news articles for an Indian stock from Yahoo Finance.

        Args:
            symbol: NSE stock symbol (e.g., 'RELIANCE'). Do not include .NS suffix.
            count: Maximum number of articles to return (default 5, max 10).

        Returns list of dicts with: title, publisher, link, publish_time.
        """
        count = min(count, MAX_NEWS_COUNT)

        err = validate_symbol(symbol)
        if err:
            return err

        return news_service.get_stock_news(symbol, count)
