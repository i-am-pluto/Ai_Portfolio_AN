"""Business logic for fundamental ratios, financial statements, and peer comparison."""

import time
from typing import Literal

from stocks_fetch.clients import yfinance_client
from stocks_fetch.constants import (
    CASH_FIELDS,
    GROWTH_FIELDS,
    LEVERAGE_FIELDS,
    MAX_PEER_SYMBOLS,
    META_FIELDS,
    PEER_FIELDS,
    PROFITABILITY_FIELDS,
    RATE_LIMIT_DELAY,
    SUMMARY_MAX_LENGTH,
    VALUATION_FIELDS,
)
from stocks_fetch.utils.symbols import validate_symbol


def _extract_fields(info: dict, field_map: dict) -> dict:
    """Extract fields from info dict using a yfinance-key -> output-key mapping."""
    return {out_key: info.get(yf_key) for yf_key, out_key in field_map.items()}


def get_fundamental_ratios(symbol: str) -> dict:
    """Fetch and structure fundamental ratios into 6 categories."""
    info = yfinance_client.fetch_info(symbol)

    summary = info.get("longBusinessSummary", "")
    if len(summary) > SUMMARY_MAX_LENGTH:
        summary = summary[: SUMMARY_MAX_LENGTH - 3] + "..."

    meta = _extract_fields(info, META_FIELDS)
    meta["summary"] = summary

    return {
        "symbol": symbol.upper(),
        "valuation": _extract_fields(info, VALUATION_FIELDS),
        "profitability": _extract_fields(info, PROFITABILITY_FIELDS),
        "leverage": _extract_fields(info, LEVERAGE_FIELDS),
        "growth": _extract_fields(info, GROWTH_FIELDS),
        "cash": _extract_fields(info, CASH_FIELDS),
        "meta": meta,
    }


def get_financial_statement(
    symbol: str,
    stmt_type: Literal["income", "balance_sheet", "cashflow"] = "income",
    quarterly: bool = False,
) -> list[dict] | str:
    """Fetch and transpose a financial statement into period-based records."""
    df = yfinance_client.fetch_statement(symbol, stmt_type, quarterly)

    if df is None:
        return f"No {stmt_type} data found for {symbol}."

    records = []
    for col in df.columns:
        period_data = {"period": col.strftime("%Y-%m-%d")}
        for item, value in df[col].items():
            if value is not None and str(value) != "nan":
                period_data[str(item)] = float(value)
            else:
                period_data[str(item)] = None
        records.append(period_data)

    return records


def compare_peers(symbols: list[str]) -> list[dict] | str:
    """Compare fundamental metrics across multiple stocks."""
    if len(symbols) > MAX_PEER_SYMBOLS:
        return f"Maximum {MAX_PEER_SYMBOLS} symbols allowed for comparison."

    results = []
    for i, sym in enumerate(symbols):
        err = validate_symbol(sym)
        if err:
            results.append({"symbol": sym.upper(), "error": err})
            if i < len(symbols) - 1:
                time.sleep(RATE_LIMIT_DELAY)
            continue

        info = yfinance_client.fetch_info(sym)

        entry = {"symbol": sym.upper()}
        for out_key, (primary, fallback) in PEER_FIELDS.items():
            value = info.get(primary)
            if value is None and fallback:
                value = info.get(fallback)
            entry[out_key] = value

        results.append(entry)

        if i < len(symbols) - 1:
            time.sleep(RATE_LIMIT_DELAY)

    return results
