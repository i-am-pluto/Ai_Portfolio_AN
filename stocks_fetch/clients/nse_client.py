"""All nselib interactions — raw data fetching, no business logic."""

from typing import Literal

import pandas as pd


def is_available() -> bool:
    """Check if nselib is installed."""
    try:
        import nselib  # noqa: F401
        return True
    except ImportError:
        return False


def fetch_corporate_actions(
    period: Literal["1D", "1W", "1M", "6M", "1Y"] = "1M",
) -> pd.DataFrame | str:
    """Fetch corporate actions from NSE. Returns DataFrame or error string."""
    try:
        from nselib import capital_market
    except ImportError:
        return "nselib is not installed. Install it with: pip install nselib"

    try:
        df = capital_market.corporate_actions_for_equity(period=period)
        if df is None or df.empty:
            return "No corporate actions data available from NSE at this time."
        return df
    except Exception as e:
        return f"Failed to fetch NSE corporate actions: {e}. NSE endpoint may be temporarily unavailable."
