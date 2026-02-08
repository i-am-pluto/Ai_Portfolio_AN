"""Business logic for dividends, splits, and NSE corporate actions."""

from typing import Literal

import pandas as pd

from stocks_fetch.clients import nse_client, yfinance_client
from stocks_fetch.constants import MAX_NSE_RECORDS


def get_dividends_and_splits(symbol: str) -> dict | str:
    """Process dividend and split history into dated records."""
    dividends = yfinance_client.fetch_dividends(symbol)
    splits = yfinance_client.fetch_splits(symbol)

    div_records = []
    if dividends is not None and not dividends.empty:
        for date, amount in dividends.items():
            div_records.append({
                "date": date.strftime("%Y-%m-%d"),
                "amount": round(float(amount), 2),
            })
        div_records.reverse()

    split_records = []
    if splits is not None and not splits.empty:
        for date, ratio in splits.items():
            split_records.append({
                "date": date.strftime("%Y-%m-%d"),
                "ratio": str(ratio),
            })
        split_records.reverse()

    if not div_records and not split_records:
        return f"No dividend or split history found for {symbol}."

    return {
        "symbol": symbol.upper(),
        "dividends": div_records,
        "splits": split_records,
    }


def get_nse_corporate_actions(
    symbol: str | None = None,
    period: Literal["1D", "1W", "1M", "6M", "1Y"] = "1M",
) -> list[dict] | str:
    """Fetch and filter NSE corporate actions."""
    result = nse_client.fetch_corporate_actions(period)

    # Client returns a string on error
    if isinstance(result, str):
        return result

    df: pd.DataFrame = result

    if symbol:
        sym_upper = symbol.upper().strip()
        for col in df.columns:
            if "symbol" in col.lower() or "company" in col.lower():
                mask = df[col].astype(str).str.upper().str.contains(sym_upper, na=False)
                df = df[mask]
                break

    records = df.head(MAX_NSE_RECORDS).to_dict(orient="records")
    return [{k: str(v) if v is not None else None for k, v in rec.items()} for rec in records]
