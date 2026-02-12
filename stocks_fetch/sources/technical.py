"""Correlation and covariance tools for portfolio diversification analysis."""

from typing import Any, Literal, TypedDict

from stocks_fetch.services import technical as technical_service


class CorrelationResult(TypedDict):
    """Structure of correlation analysis result."""

    symbols: list[str]
    correlation_matrix: list[list[float]]
    covariance_matrix: list[list[float]]
    volatility: list[float]
    mean_returns: list[float]
    metadata: dict[str, Any]


def register(mcp) -> None:
    """Register technical analysis tools on the MCP server."""

    @mcp.tool(annotations={"readOnlyHint": True})
    def get_stock_correlations(
        symbols: list[str],
        period: Literal["1mo", "3mo", "6mo", "1y", "2y", "5y"] = "1y",
        interval: Literal["1d", "1wk", "1mo"] = "1d",
        returns_type: Literal["simple", "log"] = "simple",
        annualize_covariance: bool = True,
    ) -> CorrelationResult | str:
        """Calculate stock correlation/covariance metrics for portfolio diversification.

        Args:
            symbols: List of 2-20 NSE stock symbols (e.g., ['RELIANCE', 'TCS', 'INFY']).
                     Do not include .NS suffix.
            period: Historical period for analysis.
            interval: Price frequency used for return calculation.
            returns_type: 'simple' for arithmetic returns, 'log' for log returns.
            annualize_covariance: Annualize covariance matrix using interval-based factor.

        Returns dict with:
        - symbols: normalized symbol order used in matrices
        - correlation_matrix: NxN matrix of pairwise return correlations
        - covariance_matrix: NxN matrix of return covariances
        - volatility: annualized volatility per symbol
        - mean_returns: annualized mean return per symbol
        - metadata: settings, observation count, and date coverage
        """
        return technical_service.get_stock_correlations(
            symbols=symbols,
            period=period,
            interval=interval,
            returns_type=returns_type,
            annualize_covariance=annualize_covariance,
        )
