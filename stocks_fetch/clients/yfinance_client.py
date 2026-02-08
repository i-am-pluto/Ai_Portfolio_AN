"""All yfinance interactions — raw data fetching, no business logic."""

from typing import Literal

import pandas as pd
import yfinance as yf

from stocks_fetch.utils.symbols import to_yahoo_symbol


def get_ticker(symbol: str) -> yf.Ticker:
    """Create a yfinance Ticker from an NSE symbol."""
    return yf.Ticker(to_yahoo_symbol(symbol))


def fetch_info(symbol: str) -> dict:
    """Return raw ticker.info dict."""
    return get_ticker(symbol).info


def fetch_statement(
    symbol: str,
    stmt_type: Literal["income", "balance_sheet", "cashflow"],
    quarterly: bool = False,
) -> pd.DataFrame | None:
    """Return raw financial statement DataFrame (line items as rows, periods as columns)."""
    ticker = get_ticker(symbol)

    stmt_map = {
        "income": (ticker.income_stmt, ticker.quarterly_income_stmt),
        "balance_sheet": (ticker.balance_sheet, ticker.quarterly_balance_sheet),
        "cashflow": (ticker.cashflow, ticker.quarterly_cashflow),
    }

    annual, qtr = stmt_map[stmt_type]
    df = qtr if quarterly else annual
    if df is None or df.empty:
        return None
    return df


def fetch_dividends(symbol: str) -> pd.Series:
    """Return raw ticker.dividends Series."""
    return get_ticker(symbol).dividends


def fetch_splits(symbol: str) -> pd.Series:
    """Return raw ticker.splits Series."""
    return get_ticker(symbol).splits


def fetch_news(symbol: str) -> list[dict]:
    """Return raw ticker.news list."""
    return get_ticker(symbol).news or []
