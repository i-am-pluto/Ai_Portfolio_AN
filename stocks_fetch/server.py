"""FastMCP server for Indian stock portfolio analysis."""

from fastmcp import FastMCP

mcp = FastMCP(
    name="Indian Stock Portfolio Analyzer",
    instructions=(
        "Tools for analyzing an Indian stock portfolio. "
        "All stock symbols are NSE symbols (e.g., RELIANCE, TCS, HDFCBANK). "
        "Do not include the .NS suffix — tools handle normalization automatically."
    ),
)

# Each module exports a register(mcp) function that decorates tools onto this instance.
from stocks_fetch.sources.portfolio import register as register_portfolio
from stocks_fetch.sources.price_history import register as register_price_history
from stocks_fetch.sources.fundamentals import register as register_fundamentals
from stocks_fetch.sources.corporate import register as register_corporate
from stocks_fetch.sources.market_info import register as register_market_info

register_portfolio(mcp)
register_price_history(mcp)
register_fundamentals(mcp)
register_corporate(mcp)
register_market_info(mcp)

def main():
    """Entry point for console script."""
    mcp.run()

if __name__ == "__main__":
    main()
