"""Tests for markdown report generation."""

from __future__ import annotations

from pathlib import Path

from stocks_fetch.agent.report_generator import generate_report


def test_generate_report_includes_correlation_and_covariance(tmp_path: Path) -> None:
    state = {
        "auth_status": "kite_login_triggered",
        "degraded_mode": False,
        "holdings": [{"tradingsymbol": "RELIANCE", "quantity": 10, "average_price": 2500}],
        "symbols": ["RELIANCE", "TCS"],
        "correlation_data": {
            "symbols": ["RELIANCE", "TCS"],
            "correlation_matrix": [[1.0, 0.45], [0.45, 1.0]],
            "covariance_matrix": [[0.1, 0.02], [0.02, 0.12]],
        },
        "per_symbol_analysis": {"RELIANCE": {}, "TCS": {}},
        "data_status": {
            "RELIANCE": {"fundamental_ratios": "ok", "stock_news": "ok"},
            "TCS": {"fundamental_ratios": "ok", "stock_news": "failed"},
        },
        "executive_summary": "Summary text",
        "portfolio_insights": "Detailed text",
        "errors": [],
    }

    report_path = Path(generate_report(state, tmp_path))
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "Correlation Matrix" in content
    assert "Covariance Matrix" in content
    assert "Data Coverage" in content
    assert "Portfolio Analysis Report" in content
