"""Historic price and current price tools."""

from typing import Literal

import yfinance as yf

from stocks_fetch.utils.symbols import to_yahoo_symbol


def register(mcp) -> None:
    """Register price history tools on the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_stock_price_history(
        symbol: str,
        period: Literal["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "max"] = "1y",
        interval: Literal["1d", "1wk", "1mo"] = "1d",
    ) -> list[dict] | str:
        """Get historical OHLCV price data for an Indian stock.

        Args:
            symbol: NSE stock symbol (e.g., 'RELIANCE'). Do not include .NS suffix.
            period: Time period — '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'max'.
            interval: Data interval — '1d' (daily), '1wk' (weekly), '1mo' (monthly).

        Returns list of dicts with keys: date, open, high, low, close, volume.
        """
        ticker = yf.Ticker(to_yahoo_symbol(symbol))
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            return f"No price data found for {symbol}. Check if the symbol is valid."

        df = df.reset_index()
        df = df.rename(columns={"Date": "date", "Open": "open", "High": "high",
                                "Low": "low", "Close": "close", "Volume": "volume"})
        df = df[["date", "open", "high", "low", "close", "volume"]]
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df[["open", "high", "low", "close"]] = df[["open", "high", "low", "close"]].round(2)
        df["volume"] = df["volume"].astype(int)

        return df.to_dict(orient="records")

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_current_price(symbol: str) -> dict | str:
        """Get the current/latest market price and basic price info for an Indian stock.

        Args:
            symbol: NSE stock symbol (e.g., 'RELIANCE'). Do not include .NS suffix.

        Returns dict with: symbol, current_price, previous_close, open, day_high, day_low,
        volume, fifty_two_week_high, fifty_two_week_low, market_cap.
        """
        ticker = yf.Ticker(to_yahoo_symbol(symbol))
        info = ticker.info

        if not info or info.get("regularMarketPrice") is None:
            return f"No price data found for {symbol}. Check if the symbol is valid."

        return {
            "symbol": symbol.upper(),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "open": info.get("open") or info.get("regularMarketOpen"),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "market_cap": info.get("marketCap"),
        }
