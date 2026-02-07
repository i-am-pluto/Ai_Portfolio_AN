"""Market overview and stock news tools."""

import yfinance as yf

from stocks_fetch.utils.symbols import to_yahoo_symbol


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
        count = min(count, 10)
        ticker = yf.Ticker(to_yahoo_symbol(symbol))
        news = ticker.news

        if not news:
            return f"No news found for {symbol}."

        results = []
        for item in news[:count]:
            content = item.get("content", {})
            provider = content.get("provider", {})
            click_url = content.get("clickThroughUrl", {})
            results.append({
                "title": content.get("title"),
                "publisher": provider.get("displayName"),
                "link": click_url.get("url"),
                "publish_time": content.get("pubDate"),
            })

        return results

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_market_overview() -> dict:
        """Get a snapshot of key Indian market indices (NIFTY 50 and SENSEX).

        Returns dict with current values, day change, and change percent for each index.
        """
        indices = {
            "nifty_50": "^NSEI",
            "sensex": "^BSESN",
        }

        result = {}
        for name, ticker_sym in indices.items():
            ticker = yf.Ticker(ticker_sym)
            info = ticker.info

            result[name] = {
                "price": info.get("regularMarketPrice"),
                "previous_close": info.get("regularMarketPreviousClose") or info.get("previousClose"),
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent"),
                "day_high": info.get("regularMarketDayHigh") or info.get("dayHigh"),
                "day_low": info.get("regularMarketDayLow") or info.get("dayLow"),
            }

        return result
