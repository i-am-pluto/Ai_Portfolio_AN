"""CLI runner for conversational, login-first portfolio analysis."""

from __future__ import annotations

import argparse
import asyncio
import logging
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv

from stocks_fetch.agent.config import AgentConfig
from stocks_fetch.agent.mcp_client import AgentMCPClient
from stocks_fetch.agent.state.defaults import build_initial_state
from stocks_fetch.agent.state.schema import WorkflowState
from stocks_fetch.agent.workflow.graph import create_analysis_workflow


_AUTH_PENDING_STATUSES = {"kite_login_required", "kite_login_pending"}


async def run_analysis_once(
    config: AgentConfig,
    mcp: AgentMCPClient,
    user_request: str | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> WorkflowState:
    """Run one full workflow cycle and return final state."""
    graph = create_analysis_workflow(config=config, mcp=mcp, on_progress=on_progress)
    state = await graph.ainvoke(build_initial_state(user_request))
    return WorkflowState(**state)


def _emit_workflow_warnings(
    state: WorkflowState,
    output_func: Callable[[str], Any],
) -> None:
    """Print capped workflow warnings when present."""
    if not state.get("errors"):
        return

    output_func("Workflow warnings:")
    for err in state["errors"][:10]:
        output_func(f"  - {err}")


def _emit_login_guidance(
    state: WorkflowState,
    login_attempts: int,
    output_func: Callable[[str], Any],
) -> None:
    """Print login URL or fallback payload to guide manual auth flow."""
    if login_attempts == 1:
        output_func("Kite login is required before analysis can continue.")

    login_url = state.get("kite_login_url")
    if isinstance(login_url, str) and login_url:
        output_func(f"Open this URL and complete login: {login_url}")
        return

    login_payload = state.get("kite_login_result")
    if login_attempts == 1 and login_payload is not None:
        output_func("Kite login response (URL parsing fallback):")
        output_func(str(login_payload))


def _read_login_confirmation(
    input_func: Callable[[str], str],
    output_func: Callable[[str], Any],
) -> str | None:
    """Read user confirmation after browser login."""
    try:
        return input_func(
            "Press Enter after successful Kite login (or type 'exit' to quit): "
        ).strip()
    except EOFError:
        output_func("No input available to confirm Kite login. Exiting.")
        return None
    except KeyboardInterrupt:
        output_func("\nInterrupted before Kite login completion.")
        return None


async def _resolve_kite_login_loop(
    config: AgentConfig,
    mcp: AgentMCPClient,
    initial_request: str | None,
    state: WorkflowState,
    input_func: Callable[[str], str],
    output_func: Callable[[str], Any],
) -> tuple[WorkflowState, int | None]:
    """Run login confirmation loop until auth clears or flow exits."""
    login_attempts = 0

    while state.get("auth_status") in _AUTH_PENDING_STATUSES:
        login_attempts += 1
        _emit_login_guidance(state, login_attempts, output_func)

        response = _read_login_confirmation(input_func, output_func)
        if response is None:
            return state, 1
        if response.lower() in {"exit", "quit"}:
            output_func("Session closed before Kite authentication.")
            return state, 1

        # Post-login delay: let SSE session propagate
        output_func("Waiting for session to activate...")
        await asyncio.sleep(config.auth_retry_delay)

        state = await run_analysis_once(
            config,
            mcp,
            user_request=initial_request,
            on_progress=output_func,
        )

        if login_attempts >= 5 and state.get("auth_status") in _AUTH_PENDING_STATUSES:
            output_func("Kite login is still pending after multiple attempts. Exiting.")
            _emit_workflow_warnings(state, output_func)
            return state, 1

    return state, None


def _read_conversation_request(
    input_func: Callable[[str], str],
    output_func: Callable[[str], Any],
) -> str | None:
    """Read one conversational request from CLI input."""
    try:
        return input_func("portfolio-agent> ").strip()
    except EOFError:
        output_func("Exiting conversational mode.")
        return None
    except KeyboardInterrupt:
        output_func("\nInterrupted. Exiting conversational mode.")
        return None


async def _run_conversational_mode(
    config: AgentConfig,
    mcp: AgentMCPClient,
    input_func: Callable[[str], str],
    output_func: Callable[[str], Any],
) -> None:
    """Handle conversational follow-up prompts after initial report."""
    output_func("Entering conversational mode. Type 'exit' to quit.")
    while True:
        request = _read_conversation_request(input_func, output_func)
        if request is None:
            break

        if request.lower() in {"exit", "quit"}:
            output_func("Session closed.")
            break

        followup_request = request or "Refresh analysis with latest available data."
        followup = await run_analysis_once(
            config,
            mcp,
            user_request=followup_request,
            on_progress=output_func,
        )
        output_func(f"Follow-up report: {followup.get('report_path', 'N/A')}")
        if followup.get("executive_summary"):
            output_func(followup["executive_summary"])


async def run_agent_loop(
    config: AgentConfig,
    *,
    one_shot: bool = False,
    initial_request: str | None = None,
    input_func: Callable[[str], str] = input,
    output_func: Callable[[str], Any] = print,
    mcp_client_factory: Callable[[AgentConfig], AgentMCPClient] | None = None,
) -> int:
    """Run startup analysis, then optional conversational follow-up loop."""
    client_factory = mcp_client_factory or (
        lambda cfg: AgentMCPClient(kite_sse_url=cfg.kite_sse_url, use_kite=cfg.use_kite)
    )

    async with client_factory(config) as mcp:
        output_func("Connecting to MCP servers...")
        state = await run_analysis_once(
            config, mcp, user_request=initial_request, on_progress=output_func,
        )
        state, exit_code = await _resolve_kite_login_loop(
            config=config,
            mcp=mcp,
            initial_request=initial_request,
            state=state,
            input_func=input_func,
            output_func=output_func,
        )
        if exit_code is not None:
            return exit_code

        if state.get("report_path"):
            output_func(f"Report saved to: {state['report_path']}")
        else:
            output_func("No report path produced.")

        _emit_workflow_warnings(state, output_func)

        if one_shot:
            return 0

        await _run_conversational_mode(
            config=config,
            mcp=mcp,
            input_func=input_func,
            output_func=output_func,
        )

    return 0


def run_portfolio_analysis() -> int:
    """Main CLI entrypoint for portfolio-report command."""
    load_dotenv(override=False)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="Dual-MCP portfolio analysis agent")
    parser.add_argument(
        "--one-shot",
        action="store_true",
        help="Run once (login-first auto-analysis) and exit without chat loop.",
    )
    parser.add_argument(
        "--request",
        type=str,
        default=None,
        help="Optional initial analysis request override.",
    )
    parser.add_argument(
        "--no-kite",
        action="store_true",
        help="Disable Kite MCP and run in analyzer-only degraded mode.",
    )
    args = parser.parse_args()

    config = AgentConfig.from_env(require_model_key=True)
    if args.no_kite:
        config = config.with_overrides(use_kite=False)

    return asyncio.run(
        run_agent_loop(
            config=config,
            one_shot=args.one_shot,
            initial_request=args.request,
        )
    )


if __name__ == "__main__":
    raise SystemExit(run_portfolio_analysis())
