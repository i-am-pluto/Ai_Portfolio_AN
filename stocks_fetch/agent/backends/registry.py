"""Backend registry — maps name strings to AbstractAnalysisBackend classes."""

from __future__ import annotations

from stocks_fetch.agent.backends.base import AbstractAnalysisBackend

_REGISTRY: dict[str, type[AbstractAnalysisBackend]] = {}


def register_backend(name: str, cls: type[AbstractAnalysisBackend]) -> None:
    """Register a backend class under the given name."""
    _REGISTRY[name] = cls


def get_backend(name: str = "langgraph") -> AbstractAnalysisBackend:
    """
    Return an instantiated backend by name.

    Lazily registers built-in backends on first call so that
    optional dependencies are only imported when needed.
    """
    if name not in _REGISTRY:
        from stocks_fetch.agent.backends.langgraph_backend import LangGraphBackend

        register_backend("langgraph", LangGraphBackend)

    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY)) or "none"
        raise ValueError(f"Unknown AI backend: {name!r}. Available: {available}")

    return _REGISTRY[name]()
