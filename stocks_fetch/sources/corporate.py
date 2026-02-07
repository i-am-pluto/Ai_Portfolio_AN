"""Corporate actions, dividends, and splits tools."""

import yfinance as yf

from stocks_fetch.utils.symbols import to_yahoo_symbol


def register(mcp) -> None:
    """Register corporate action tools on the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_dividends_and_splits(symbol: str) -> dict | str:
        """Get dividend and stock split history for an Indian stock.

        Args:
            symbol: NSE stock symbol (e.g., 'ITC'). Do not include .NS suffix.

        Returns dict with:
        - dividends: list of {date, amount} sorted most recent first
        - splits: list of {date, ratio} sorted most recent first
        """
        ticker = yf.Ticker(to_yahoo_symbol(symbol))

        dividends = ticker.dividends
        splits = ticker.splits

        div_records = []
        if dividends is not None and not dividends.empty:
            for date, amount in dividends.items():
                div_records.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "amount": round(float(amount), 2),
                })
            div_records.reverse()  # Most recent first

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

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_nse_corporate_actions(
        symbol: str | None = None,
    ) -> list[dict] | str:
        """Get recent and upcoming corporate actions from NSE (dividends, splits, bonuses).

        Args:
            symbol: Optional NSE stock symbol to filter by. If None, returns recent actions
                    across all stocks.

        Returns list of dicts with corporate action details.
        Note: This uses the nselib library which depends on NSE website availability.
        If NSE endpoints are down, returns an error message.
        """
        try:
            from nselib import capital_market
        except ImportError:
            return "nselib is not installed. Install it with: pip install nselib"

        try:
            df = capital_market.corporate_actions(segment="equities")

            if df is None or df.empty:
                return "No corporate actions data available from NSE at this time."

            if symbol:
                sym_upper = symbol.upper().strip()
                # Try to filter by symbol column — column names vary by nselib version
                for col in df.columns:
                    if "symbol" in col.lower() or "company" in col.lower():
                        mask = df[col].astype(str).str.upper().str.contains(sym_upper, na=False)
                        df = df[mask]
                        break

            records = df.head(25).to_dict(orient="records")
            # Convert any non-serializable types
            clean = []
            for rec in records:
                clean.append({k: str(v) if v is not None else None for k, v in rec.items()})
            return clean

        except Exception as e:
            return f"Failed to fetch NSE corporate actions: {e}. NSE endpoint may be temporarily unavailable."
