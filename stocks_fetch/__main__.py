"""Allow running as `python -m stocks_fetch`."""
from stocks_fetch.server import mcp

if __name__ == "__main__":
    mcp.run()
