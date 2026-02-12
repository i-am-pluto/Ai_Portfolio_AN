"""Tests for correlation/covariance analysis service and source wrapper."""

from __future__ import annotations

import numpy as np
import pandas as pd

from stocks_fetch.services.technical import get_stock_correlations


def _fake_download(*args, **kwargs) -> pd.DataFrame:  # type: ignore[no-untyped-def]
    dates = pd.date_range("2025-01-01", periods=6, freq="D")
    columns = pd.MultiIndex.from_tuples(
        [
            ("Adj Close", "RELIANCE.NS"),
            ("Adj Close", "TCS.NS"),
            ("Adj Close", "INFY.NS"),
        ]
    )
    data = np.array(
        [
            [2500.0, 4000.0, 1800.0],
            [2525.0, 4010.0, 1815.0],
            [2510.0, 4050.0, 1830.0],
            [2540.0, 4040.0, 1840.0],
            [2560.0, 4070.0, 1835.0],
            [2585.0, 4095.0, 1855.0],
        ]
    )
    return pd.DataFrame(data, index=dates, columns=columns)


def test_get_stock_correlations_returns_square_matrices(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setattr("stocks_fetch.services.technical.yf.download", _fake_download)

    result = get_stock_correlations(symbols=["RELIANCE", "TCS", "INFY"])
    assert isinstance(result, dict)
    assert result["symbols"] == ["RELIANCE", "TCS", "INFY"]

    corr = result["correlation_matrix"]
    cov = result["covariance_matrix"]
    assert len(corr) == 3
    assert len(cov) == 3
    assert all(len(row) == 3 for row in corr)
    assert all(len(row) == 3 for row in cov)
    assert result["metadata"]["observations"] > 0


def test_get_stock_correlations_requires_two_symbols() -> None:
    result = get_stock_correlations(symbols=["RELIANCE"])
    assert isinstance(result, str)
    assert "At least 2 symbols" in result
