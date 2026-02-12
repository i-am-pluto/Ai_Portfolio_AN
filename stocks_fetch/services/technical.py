"""Correlation and covariance analysis service for portfolio analytics."""

from typing import Literal

import numpy as np
import pandas as pd
import yfinance as yf

from stocks_fetch.utils.symbols import to_yahoo_symbol

_MAX_SYMBOLS = 20
_MIN_SYMBOLS = 2


def _annualization_factor(interval: str) -> int:
    """Return annualization factor for return volatility/covariance scaling."""
    return {"1d": 252, "1wk": 52, "1mo": 12}.get(interval, 252)


def _normalize_symbols(symbols: list[str]) -> list[str]:
    """Normalize symbols to uppercase and remove duplicates while preserving order."""
    normalized: list[str] = []
    seen: set[str] = set()
    for symbol in symbols:
        clean = symbol.upper().strip()
        if clean and clean not in seen:
            normalized.append(clean)
            seen.add(clean)
    return normalized


def _extract_price_frame(
    downloaded: pd.DataFrame, yahoo_symbols: list[str], symbols: list[str]
) -> pd.DataFrame:
    """Extract a symbol-aligned close-price frame from yfinance download output."""
    if downloaded.empty:
        return pd.DataFrame()

    if isinstance(downloaded.columns, pd.MultiIndex):
        fields = downloaded.columns.get_level_values(0)
        if "Adj Close" in fields:
            price_frame = downloaded["Adj Close"].copy()
        elif "Close" in fields:
            price_frame = downloaded["Close"].copy()
        else:
            return pd.DataFrame()
    else:
        if "Adj Close" in downloaded.columns:
            price_frame = downloaded[["Adj Close"]].copy()
            price_frame.columns = [yahoo_symbols[0]]
        elif "Close" in downloaded.columns:
            price_frame = downloaded[["Close"]].copy()
            price_frame.columns = [yahoo_symbols[0]]
        else:
            return pd.DataFrame()

    symbol_map = dict(zip(yahoo_symbols, symbols, strict=False))
    price_frame = price_frame.rename(columns=symbol_map)

    existing = [symbol for symbol in symbols if symbol in price_frame.columns]
    if not existing:
        return pd.DataFrame()

    return price_frame[existing].dropna(how="all")


def get_stock_correlations(
    symbols: list[str],
    period: Literal["1mo", "3mo", "6mo", "1y", "2y", "5y"] = "1y",
    interval: Literal["1d", "1wk", "1mo"] = "1d",
    returns_type: Literal["simple", "log"] = "simple",
    annualize_covariance: bool = True,
) -> dict | str:
    """Calculate correlation and covariance matrices for a list of stocks."""
    normalized = _normalize_symbols(symbols)

    if len(normalized) < _MIN_SYMBOLS:
        return "Error: At least 2 symbols required for correlation analysis."
    if len(normalized) > _MAX_SYMBOLS:
        return f"Error: Maximum {_MAX_SYMBOLS} symbols allowed."

    yahoo_symbols = [to_yahoo_symbol(symbol) for symbol in normalized]

    try:
        downloaded = yf.download(
            tickers=" ".join(yahoo_symbols),
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=False,
            threads=True,
            group_by="column",
        )
    except Exception as exc:
        return f"Error: Failed to fetch historical prices: {exc}"

    prices = _extract_price_frame(downloaded, yahoo_symbols, normalized)
    if prices.empty:
        return "Error: Could not extract price data for provided symbols."

    # Forward fill sparse holidays and drop unresolved rows for aligned returns.
    prices = prices.sort_index().ffill().dropna(how="any")
    if prices.shape[0] < 3:
        return "Error: Insufficient price observations for correlation calculation."

    if returns_type == "log":
        returns = np.log(prices / prices.shift(1)).dropna(how="any")
    else:
        returns = prices.pct_change().dropna(how="any")

    if returns.empty or returns.shape[0] < 2:
        return "Error: Insufficient return observations for correlation calculation."

    factor = _annualization_factor(interval)
    correlation = returns.corr()
    covariance = returns.cov()
    if annualize_covariance:
        covariance = covariance * factor

    annualized_volatility = returns.std(ddof=1) * np.sqrt(factor)
    annualized_mean_returns = returns.mean() * factor

    return {
        "symbols": list(returns.columns),
        "correlation_matrix": correlation.round(6).values.tolist(),
        "covariance_matrix": covariance.round(10).values.tolist(),
        "volatility": [float(annualized_volatility[symbol]) for symbol in returns.columns],
        "mean_returns": [
            float(annualized_mean_returns[symbol]) for symbol in returns.columns
        ],
        "metadata": {
            "returns_type": returns_type,
            "period": period,
            "interval": interval,
            "annualize_covariance": annualize_covariance,
            "annualization_factor": factor,
            "observations": int(returns.shape[0]),
            "price_start": str(prices.index.min().date()),
            "price_end": str(prices.index.max().date()),
        },
    }
