"""LangGraph + Groq backend — wraps the existing 6-node workflow."""

from __future__ import annotations

from pathlib import Path

from stocks_fetch.agent.backends.base import AbstractAnalysisBackend
from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.mcp_client import AgentMCPClient
from stocks_fetch.agent.state.defaults import build_initial_state
from stocks_fetch.agent.workflow.graph import create_analysis_workflow


class LangGraphBackend(AbstractAnalysisBackend):
    """Runs the full LangGraph 6-node pipeline (authenticate → report)."""

    async def run_analysis(
        self,
        request: str,
        use_kite: bool = True,
        symbols: list[str] | None = None,
    ) -> str:
        config = AgentConfig.from_env(require_model_key=True)
        config = config.with_overrides(use_kite=use_kite)

        async with AgentMCPClient(
            kite_sse_url=config.kite_sse_url,
            use_kite=use_kite,
        ) as mcp:
            graph = create_analysis_workflow(config=config, mcp=mcp)
            initial_state = build_initial_state(request)

            # Seed symbols when Kite is disabled or caller provides an override list.
            if symbols:
                initial_state["symbols"] = list(symbols)

            final_state = await graph.ainvoke(initial_state)

            # Prefer the written report file; fall back to in-state content.
            report_path = final_state.get("report_path", "")
            if report_path:
                path = Path(report_path)
                if path.exists():
                    return path.read_text(encoding="utf-8")

            content_parts: list[str] = []
            if final_state.get("portfolio_insights"):
                content_parts.append(final_state["portfolio_insights"])
            if final_state.get("executive_summary"):
                content_parts.append(f"\n## Summary\n{final_state['executive_summary']}")

            errors = final_state.get("errors") or []
            if errors:
                content_parts.append(
                    "\n## Workflow Warnings\n" + "\n".join(f"- {e}" for e in errors[:10])
                )

            if content_parts:
                return "\n".join(content_parts)

            return (
                "Analysis completed but no report content was generated. "
                "Check server logs for details."
            )
