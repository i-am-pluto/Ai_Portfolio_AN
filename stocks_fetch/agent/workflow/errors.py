"""Workflow-specific error helpers and classification."""

from __future__ import annotations

import re

from stocks_fetch.agent.state.schema import WorkflowState


class WorkflowError(Exception):
    """Workflow execution error."""


_AUTH_ERROR_PATTERNS = [
    "session",
    "unauthorized",
    "unauthenticated",
    "login",
    "token expired",
    "forbidden",
    "403",
    "401",
    "access denied",
]

_TRANSIENT_ERROR_PATTERNS = [
    "timeout",
    "timed out",
    "connection reset",
    "503",
    "429",
    "service unavailable",
    "rate limit",
    "retry",
    "eof",
    "broken pipe",
    "connection refused",
]


def _is_auth_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(pattern in msg for pattern in _AUTH_ERROR_PATTERNS)


def _is_transient_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(pattern in msg for pattern in _TRANSIENT_ERROR_PATTERNS)


def _sanitize_error(message: str) -> str:
    """Truncate and clean error messages for state storage."""
    cleaned = re.sub(r"<[^>]+>", "", message)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:200] + "..." if len(cleaned) > 200 else cleaned


def append_error(state: WorkflowState, message: str) -> None:
    """Append a sanitized error to workflow state."""
    errors = list(state.get("errors", []))
    errors.append(_sanitize_error(message))
    state["errors"] = errors
