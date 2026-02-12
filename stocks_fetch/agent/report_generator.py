"""Generate markdown portfolio analysis reports."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from stocks_fetch.agent.state.schema import WorkflowState

_MAX_ERRORS_IN_REPORT = 10


def _fmt(value: Any, decimals: int = 2) -> str:
    """Format numeric values for display."""
    if value is None:
        return "N/A"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        return f"{value:,.{decimals}f}"
    return str(value)


def _matrix_to_table(title: str, symbols: list[str], matrix: list[list[Any]]) -> str:
    """Render a matrix as markdown table."""
    if not symbols or not matrix:
        return f"### {title}\nNo data available.\n"

    header = "| Symbol | " + " | ".join(symbols) + " |"
    sep = "|" + " --- |" * (len(symbols) + 1)
    rows = []
    for i, row_symbol in enumerate(symbols):
        row_values = matrix[i] if i < len(matrix) else []
        rendered = [
            _fmt(row_values[j], 4) if j < len(row_values) else "N/A"
            for j in range(len(symbols))
        ]
        rows.append("| " + row_symbol + " | " + " | ".join(rendered) + " |")

    return "\n".join([f"### {title}", header, sep, *rows, ""])


def _holding_to_row(holding: dict[str, Any]) -> str:
    """Render a holding record as markdown row."""
    symbol = str(
        holding.get("tradingsymbol")
        or holding.get("symbol")
        or holding.get("ticker")
        or holding.get("instrument")
        or "N/A"
    )
    quantity = _fmt(holding.get("quantity") or holding.get("qty") or holding.get("t1_quantity"))
    avg_price = _fmt(holding.get("average_price") or holding.get("avg_price"))
    pnl = _fmt(holding.get("pnl") or holding.get("unrealised") or holding.get("unrealized"))
    return f"| {symbol} | {quantity} | {avg_price} | {pnl} |"


def _data_coverage_table(state: WorkflowState) -> list[str]:
    """Build a data coverage table from data_status."""
    data_status = state.get("data_status", {})
    if not data_status:
        return ["No data collection status available.", ""]

    all_keys: list[str] = []
    for statuses in data_status.values():
        for k in statuses:
            if k not in all_keys:
                all_keys.append(k)

    if not all_keys:
        return ["No data collection status available.", ""]

    header = "| Symbol | " + " | ".join(all_keys) + " |"
    sep = "|" + " --- |" * (len(all_keys) + 1)
    rows = []
    for symbol, statuses in data_status.items():
        cells = []
        for key in all_keys:
            status = statuses.get(key, "-")
            cells.append(status)
        rows.append("| " + symbol + " | " + " | ".join(cells) + " |")

    return [header, sep, *rows, ""]


def generate_report(state: WorkflowState, output_dir: Path) -> str:
    """Generate markdown report from workflow state and return output path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_date = date.today().isoformat()
    report_path = output_dir / f"portfolio_analysis_{report_date}.md"

    holdings = state.get("holdings", [])
    symbols = state.get("symbols", [])
    correlation_data = state.get("correlation_data", {})
    if not isinstance(correlation_data, dict):
        correlation_data = {}

    correlation_matrix = correlation_data.get("correlation_matrix", [])
    covariance_matrix = correlation_data.get("covariance_matrix", [])
    matrix_symbols = correlation_data.get("symbols", symbols)
    errors = state.get("errors", [])

    lines: list[str] = [
        "# Portfolio Analysis Report",
        "",
        f"- **Report Date**: {report_date}",
        f"- **Auth Status**: {state.get('auth_status', 'unknown')}",
        f"- **Degraded Mode**: {state.get('degraded_mode', False)}",
        "",
        "## Holdings Snapshot",
    ]

    if holdings:
        lines.extend(
            [
                "| Symbol | Quantity | Avg Price | PnL |",
                "| --- | ---: | ---: | ---: |",
                *[_holding_to_row(holding) for holding in holdings],
                "",
            ]
        )
    else:
        lines.extend(["No holdings data available. Running in degraded mode or Kite not connected.", ""])

    lines.extend(
        [
            "## Data Coverage",
            "",
            *_data_coverage_table(state),
            "## Portfolio-Level Metrics",
            _matrix_to_table("Correlation Matrix", matrix_symbols, correlation_matrix),
            _matrix_to_table("Covariance Matrix", matrix_symbols, covariance_matrix),
            "## Per-Stock Analysis",
        ]
    )

    per_symbol = state.get("per_symbol_analysis", {})
    if isinstance(per_symbol, dict) and per_symbol:
        for symbol in symbols:
            details = per_symbol.get(symbol, {})
            fundamentals = details.get("fundamentals", {}) if isinstance(details, dict) else {}
            # Also check under fundamental_ratios key
            if not fundamentals and isinstance(details, dict):
                fundamentals = details.get("fundamental_ratios", {})
            valuation = fundamentals.get("valuation", {}) if isinstance(fundamentals, dict) else {}
            profitability = (
                fundamentals.get("profitability", {}) if isinstance(fundamentals, dict) else {}
            )
            news = details.get("news", []) if isinstance(details, dict) else []
            # Also check under stock_news key
            if not news and isinstance(details, dict):
                news = details.get("stock_news", [])
            lines.extend(
                [
                    f"### {symbol}",
                    f"- PE: {_fmt(valuation.get('pe_trailing'))}",
                    f"- PB: {_fmt(valuation.get('pb'))}",
                    f"- ROE: {_fmt(profitability.get('roe'), 4)}",
                    f"- Latest News Count: {len(news) if isinstance(news, list) else 0}",
                    "",
                ]
            )
    else:
        lines.extend(["No symbol-level analysis available.", ""])

    lines.extend(
        [
            "## Executive Summary",
            state.get("executive_summary", "Not generated."),
            "",
            "## Detailed Insights",
            state.get("portfolio_insights", "Not generated."),
            "",
            "## Notes & Warnings",
        ]
    )

    if errors:
        capped = errors[:_MAX_ERRORS_IN_REPORT]
        lines.extend([f"- {error}" for error in capped])
        remaining = len(errors) - _MAX_ERRORS_IN_REPORT
        if remaining > 0:
            lines.append(f"- ... and {remaining} more warnings (see logs for details)")
    else:
        lines.append("- No workflow errors reported.")

    lines.extend(["", "*Report generated by AI Stock Analyzer*"])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return str(report_path)
