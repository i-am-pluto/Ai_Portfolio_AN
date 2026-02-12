"""Business logic for stock news."""

from stocks_fetch.clients import yfinance_client


def get_stock_news(symbol: str, count: int = 5) -> list[dict] | str:
    """Fetch and flatten news articles for a stock."""
    raw_news = yfinance_client.fetch_news(symbol)

    if not raw_news:
        return f"No news found for {symbol}."

    results = []
    for item in raw_news[:count]:
        if not isinstance(item, dict):
            continue
        content = item.get("content") or {}
        if not isinstance(content, dict):
            continue
        provider = content.get("provider") or {}
        click_url = content.get("clickThroughUrl") or {}
        results.append({
            "title": content.get("title"),
            "publisher": provider.get("displayName"),
            "link": click_url.get("url"),
            "publish_time": content.get("pubDate"),
        })

    return results
