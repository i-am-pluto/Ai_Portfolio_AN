"""FastMCP server for Indian stock analysis — fundamentals, corporate actions & news."""

from fastmcp import FastMCP

mcp = FastMCP(
    name="Indian Stock Analyzer",
    instructions=(
        "Analytical tools for Indian stocks — fundamentals, financial statements, "
        "peer comparison, corporate actions, and news. "
        "For portfolio data, real-time prices, and trading, use the Kite MCP server. "
        "All stock symbols are NSE symbols (e.g., RELIANCE, TCS, HDFCBANK). "
        "Do not include the .NS suffix — tools handle normalization automatically."
    ),
)

# Each module exports a register(mcp) function that decorates tools onto this instance.
from stocks_fetch.sources.fundamentals import register as register_fundamentals
from stocks_fetch.sources.corporate import register as register_corporate
from stocks_fetch.sources.market_info import register as register_market_info
from stocks_fetch.sources.technical import register as register_technical

register_fundamentals(mcp)
register_corporate(mcp)
register_market_info(mcp)
register_technical(mcp)

def main():
    """Entry point for console script."""
    mcp.run()

if __name__ == "__main__":
    main()
