"""Symbol normalization and filtering helpers."""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_ISIN_PATTERN = re.compile(r"^INF?\d{3,}")
_NON_EQUITY_PATTERNS = re.compile(
    r"^(INF|MF|SGB|LIQUIDBEES|NIFTYBEES|N\d{5}|REC-N\d|.*-SG$)",
    re.IGNORECASE,
)


def is_equity_symbol(symbol: str) -> bool:
    """Filter out ISINs, mutual fund codes, sovereign gold bonds, and ETFs."""
    if _ISIN_PATTERN.match(symbol):
        return False
    if _NON_EQUITY_PATTERNS.match(symbol):
        return False
    if len(symbol) > 20:
        return False
    return True


def extract_symbol(record: dict[str, Any]) -> str | None:
    """Extract and normalize symbol fields from a holdings/positions record."""
    for key in ("tradingsymbol", "symbol", "ticker", "instrument", "stock"):
        value = record.get(key)
        if not value:
            continue
        raw = str(value).strip().upper()
        if ":" in raw:
            raw = raw.split(":")[-1]
        if raw.endswith(".NS") or raw.endswith(".BO"):
            raw = raw.rsplit(".", 1)[0]
        if raw and is_equity_symbol(raw):
            return raw
        if raw:
            logger.info("Skipping non-equity symbol: %s (from record key '%s')", raw, key)
            return None
    return None


def extract_unique_symbols(holdings: list[dict[str, Any]]) -> list[str]:
    """Extract deduplicated equity symbols from holdings records."""
    logger.info("Raw holdings received: %d records", len(holdings))
    for index, record in enumerate(holdings):
        symbol = record.get("tradingsymbol") or record.get("symbol") or "?"
        quantity = record.get("quantity") or record.get("qty") or "?"
        logger.info("  holding[%d]: symbol=%s qty=%s", index, symbol, quantity)

    symbols: list[str] = []
    seen: set[str] = set()
    for record in holdings:
        symbol = extract_symbol(record)
        if symbol and symbol not in seen:
            symbols.append(symbol)
            seen.add(symbol)

    logger.info("Extracted equity symbols: %s", symbols)
    return symbols
