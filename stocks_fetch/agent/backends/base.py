"""Abstract base class for portfolio analysis backends."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractAnalysisBackend(ABC):
    """Common interface for all portfolio analysis backends."""

    @abstractmethod
    async def run_analysis(
        self,
        request: str,
        use_kite: bool = True,
        symbols: list[str] | None = None,
    ) -> str:
        """
        Run portfolio analysis and return the full report as a string.

        Args:
            request: Natural language analysis request.
            use_kite: Whether to fetch live holdings from Kite MCP.
            symbols: Override/seed symbol list (used when use_kite=False).

        Returns:
            Markdown-formatted analysis report.
        """
        ...
