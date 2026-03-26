"""Configuration for the dual-MCP portfolio analysis agent."""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

DEFAULT_LLM_PROVIDER = "groq"
SUPPORTED_LLM_PROVIDERS = {"groq", "grok", "xai"}
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
DEFAULT_GROK_MODEL = "grok-2-latest"
DEFAULT_XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_KITE_SSE_URL = "https://mcp.kite.trade/sse"

# MCP server transport settings (for SSE / cloud deployment)
DEFAULT_MCP_TRANSPORT = "stdio"   # "stdio" | "sse"
DEFAULT_MCP_HOST = "0.0.0.0"
DEFAULT_MCP_PORT = 8000

# Pluggable AI backend
DEFAULT_AI_BACKEND = "langgraph"  # "langgraph" | future: "claude_api"


def _env_bool(name: str, default: bool) -> bool:
    """Read boolean environment values with common true/false spellings."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    lowered = raw.strip().lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    return default


@dataclass(frozen=True)
class AgentConfig:
    """Runtime configuration for analysis workflow and model backend."""

    llm_provider: str = DEFAULT_LLM_PROVIDER
    groq_api_key: str = ""
    groq_model: str = DEFAULT_GROQ_MODEL
    grok_api_key: str = ""
    grok_model: str = DEFAULT_GROK_MODEL
    xai_base_url: str = DEFAULT_XAI_BASE_URL
    use_kite: bool = True
    kite_sse_url: str = DEFAULT_KITE_SSE_URL
    correlation_period: str = "1y"
    correlation_interval: str = "1d"
    correlation_returns_type: str = "simple"
    auth_retry_delay: float = 3.0
    tool_retry_delay: float = 2.0
    report_dir: Path = Path("reports")
    # MCP server transport (used by server.py main())
    mcp_transport: str = DEFAULT_MCP_TRANSPORT
    mcp_host: str = DEFAULT_MCP_HOST
    mcp_port: int = DEFAULT_MCP_PORT
    # Pluggable AI backend for trigger_portfolio_analysis
    ai_backend: str = DEFAULT_AI_BACKEND

    @classmethod
    def from_env(cls, require_model_key: bool = True) -> AgentConfig:
        """Create config from environment with validation and defaults."""
        provider = os.environ.get("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower()
        if provider not in SUPPORTED_LLM_PROVIDERS:
            supported = ", ".join(sorted(SUPPORTED_LLM_PROVIDERS))
            raise ValueError(f"LLM_PROVIDER must be one of: {supported}.")

        groq_api_key = os.environ.get("GROQ_API_KEY", "").strip()
        grok_api_key = (
            os.environ.get("GROK_API_KEY", "").strip() or os.environ.get("XAI_API_KEY", "").strip()
        )

        if require_model_key:
            if provider == "groq" and not groq_api_key:
                raise ValueError("GROQ_API_KEY environment variable not set for LLM_PROVIDER=groq.")
            if provider in {"grok", "xai"} and not grok_api_key:
                raise ValueError(
                    "GROK_API_KEY (or XAI_API_KEY) environment variable not set for "
                    f"LLM_PROVIDER={provider}."
                )

        groq_model = os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL).strip()
        if not groq_model:
            groq_model = DEFAULT_GROQ_MODEL
        grok_model = (
            os.environ.get("GROK_MODEL", "").strip()
            or os.environ.get("XAI_MODEL", "").strip()
            or DEFAULT_GROK_MODEL
        )

        report_dir_raw = os.environ.get("PORTFOLIO_REPORT_DIR", "reports").strip() or "reports"
        report_dir = Path(report_dir_raw)

        return cls(
            llm_provider=provider,
            groq_api_key=groq_api_key,
            groq_model=groq_model,
            grok_api_key=grok_api_key,
            grok_model=grok_model,
            xai_base_url=os.environ.get("XAI_BASE_URL", DEFAULT_XAI_BASE_URL).strip()
            or DEFAULT_XAI_BASE_URL,
            use_kite=_env_bool("USE_KITE", True),
            kite_sse_url=os.environ.get("KITE_SSE_URL", DEFAULT_KITE_SSE_URL).strip()
            or DEFAULT_KITE_SSE_URL,
            correlation_period=os.environ.get("CORRELATION_PERIOD", "1y").strip() or "1y",
            correlation_interval=os.environ.get("CORRELATION_INTERVAL", "1d").strip() or "1d",
            correlation_returns_type=os.environ.get("CORRELATION_RETURNS_TYPE", "simple").strip()
            or "simple",
            report_dir=report_dir,
            mcp_transport=os.environ.get("MCP_TRANSPORT", DEFAULT_MCP_TRANSPORT).strip().lower()
            or DEFAULT_MCP_TRANSPORT,
            mcp_host=os.environ.get("MCP_HOST", DEFAULT_MCP_HOST).strip() or DEFAULT_MCP_HOST,
            mcp_port=int(
                os.environ.get("MCP_PORT", os.environ.get("PORT", str(DEFAULT_MCP_PORT)))
            ),
            ai_backend=os.environ.get("AI_BACKEND", DEFAULT_AI_BACKEND).strip()
            or DEFAULT_AI_BACKEND,
        )

    def with_overrides(
        self,
        *,
        use_kite: bool | None = None,
        report_dir: Path | None = None,
    ) -> AgentConfig:
        """Return a copy with selective runtime overrides."""
        return replace(
            self,
            use_kite=self.use_kite if use_kite is None else use_kite,
            report_dir=self.report_dir if report_dir is None else report_dir,
        )
