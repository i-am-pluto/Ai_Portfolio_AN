"""Portfolio CSV reader tools."""

import os
from pathlib import Path

import pandas as pd


_CSV_PATH = Path(
    os.environ.get(
        "PORTFOLIO_CSV",
        Path(__file__).resolve().parent.parent.parent / "data" / "portfolio.csv",
    )
)


def _read_portfolio() -> pd.DataFrame:
    """Read the portfolio CSV into a DataFrame."""
    if not _CSV_PATH.exists():
        raise FileNotFoundError(f"Portfolio CSV not found at {_CSV_PATH}")
    return pd.read_csv(_CSV_PATH, parse_dates=["buy_date"])


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to list of dicts with JSON-safe types."""
    df = df.copy()
    if "buy_date" in df.columns:
        df["buy_date"] = df["buy_date"].dt.strftime("%Y-%m-%d")
    # Fill NaN with None for clean JSON
    df = df.where(df.notna(), None)
    return df.to_dict(orient="records")


def register(mcp) -> None:
    """Register portfolio tools on the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_portfolio() -> list[dict]:
        """Read the complete portfolio. Returns all holdings as a list of dicts
        with keys: symbol, exchange, quantity, avg_price, buy_date, sector, notes."""
        df = _read_portfolio()
        return _df_to_records(df)

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_holding(symbol: str) -> dict | str:
        """Get details for a single stock in the portfolio.
        Returns the holding dict or an error message if the symbol is not found.

        Args:
            symbol: NSE stock symbol (e.g., 'RELIANCE', 'TCS'). Case-insensitive.
        """
        df = _read_portfolio()
        match = df[df["symbol"].str.upper() == symbol.upper().strip()]
        if match.empty:
            return f"{symbol.upper()} not found in portfolio"
        return _df_to_records(match)[0]

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_portfolio_summary() -> dict:
        """Get portfolio summary: total invested amount, number of holdings,
        sector breakdown (count and invested amount per sector), and list of all symbols."""
        df = _read_portfolio()
        df["invested"] = df["quantity"] * df["avg_price"]

        sector_groups = df.groupby("sector").agg(
            count=("symbol", "size"),
            invested=("invested", "sum"),
        )
        sector_breakdown = {
            sector: {"count": int(row["count"]), "invested": round(row["invested"], 2)}
            for sector, row in sector_groups.iterrows()
        }

        return {
            "total_invested": round(df["invested"].sum(), 2),
            "num_holdings": len(df),
            "symbols": df["symbol"].tolist(),
            "sector_breakdown": sector_breakdown,
        }

    @mcp.tool(annotations={"readOnlyHint": True})
    def search_holdings(
        sector: str | None = None,
        min_invested: float | None = None,
        max_invested: float | None = None,
    ) -> list[dict]:
        """Filter portfolio holdings by criteria. All parameters are optional.

        Args:
            sector: Filter by sector (case-insensitive partial match, e.g., 'IT' or 'bank').
            min_invested: Minimum total invested amount (quantity * avg_price).
            max_invested: Maximum total invested amount (quantity * avg_price).
        """
        df = _read_portfolio()
        df["invested"] = df["quantity"] * df["avg_price"]

        if sector is not None:
            df = df[df["sector"].str.contains(sector, case=False, na=False)]
        if min_invested is not None:
            df = df[df["invested"] >= min_invested]
        if max_invested is not None:
            df = df[df["invested"] <= max_invested]

        df = df.drop(columns=["invested"])
        return _df_to_records(df)
