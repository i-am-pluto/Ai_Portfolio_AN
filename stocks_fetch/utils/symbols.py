"""NSE/BSE symbol normalization for Yahoo Finance tickers."""

import yfinance as yf

_EXCHANGE_SUFFIX = {
    "NSE": ".NS",
    "BSE": ".BO",
}


def to_yahoo_symbol(symbol: str, exchange: str = "NSE") -> str:
    """Convert an NSE/BSE symbol to a Yahoo Finance ticker.

    Examples:
        to_yahoo_symbol("RELIANCE") -> "RELIANCE.NS"
        to_yahoo_symbol("TCS", "BSE") -> "TCS.BO"
        to_yahoo_symbol("INFY.NS") -> "INFY.NS"  # already suffixed
    """
    symbol = symbol.upper().strip()
    if symbol.endswith((".NS", ".BO")):
        return symbol
    suffix = _EXCHANGE_SUFFIX.get(exchange.upper(), ".NS")
    return f"{symbol}{suffix}"


def validate_symbol(symbol: str) -> str | None:
    """Check if a symbol resolves to valid data on Yahoo Finance.

    Returns None if valid, or an error message string if invalid.
    """
    yahoo_sym = to_yahoo_symbol(symbol)
    ticker = yf.Ticker(yahoo_sym)
    hist = ticker.history(period="1mo")
    if hist is None or hist.empty:
        return (
            f"No data found for '{symbol}'. This may not be a valid NSE symbol "
            f"— check spelling on nseindia.com (e.g., ASIANPAINT not ASIANPAINTS)."
        )
    return None
