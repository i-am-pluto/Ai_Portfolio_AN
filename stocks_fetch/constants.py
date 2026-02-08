"""Magic numbers, field mappings, and configuration constants."""

MAX_PEER_SYMBOLS = 10
MAX_NEWS_COUNT = 10
RATE_LIMIT_DELAY = 0.5  # seconds between yfinance calls in peer comparison
SUMMARY_MAX_LENGTH = 500
MAX_NSE_RECORDS = 25

# yfinance info keys -> our output field names, grouped by category

VALUATION_FIELDS = {
    "trailingPE": "pe_trailing",
    "forwardPE": "pe_forward",
    "priceToBook": "pb",
    "dividendYield": "dividend_yield",
    "marketCap": "market_cap",
}

PROFITABILITY_FIELDS = {
    "returnOnEquity": "roe",
    "returnOnAssets": "roa",
    "profitMargins": "profit_margins",
    "operatingMargins": "operating_margins",
    "grossMargins": "gross_margins",
}

LEVERAGE_FIELDS = {
    "debtToEquity": "debt_to_equity",
    "currentRatio": "current_ratio",
    "quickRatio": "quick_ratio",
}

GROWTH_FIELDS = {
    "revenueGrowth": "revenue_growth",
    "earningsGrowth": "earnings_growth",
}

CASH_FIELDS = {
    "operatingCashflow": "operating_cashflow",
    "freeCashflow": "free_cashflow",
}

META_FIELDS = {
    "sector": "sector",
    "industry": "industry",
    "fullTimeEmployees": "employees",
}

# Fields for peer comparison with fallback support: (primary_key, fallback_key | None)
PEER_FIELDS = {
    "current_price": ("currentPrice", "regularMarketPrice"),
    "market_cap": ("marketCap", None),
    "pe": ("trailingPE", None),
    "pb": ("priceToBook", None),
    "roe": ("returnOnEquity", None),
    "debt_to_equity": ("debtToEquity", None),
    "dividend_yield": ("dividendYield", None),
    "revenue_growth": ("revenueGrowth", None),
    "profit_margins": ("profitMargins", None),
}
