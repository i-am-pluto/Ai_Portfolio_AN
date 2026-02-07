"""NSE/BSE symbol normalization for Yahoo Finance tickers."""

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
