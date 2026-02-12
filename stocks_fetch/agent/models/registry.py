"""Registry for pluggable model providers."""

from __future__ import annotations

from stocks_fetch.agent.models.base import ProviderBuilder

_PROVIDERS: dict[str, ProviderBuilder] = {}


def register_provider(name: str, builder: ProviderBuilder) -> None:
    """Register a provider builder by normalized name."""
    _PROVIDERS[name.strip().lower()] = builder


def get_provider(name: str) -> ProviderBuilder:
    """Resolve a provider builder or raise a helpful error."""
    normalized = name.strip().lower()
    provider = _PROVIDERS.get(normalized)
    if provider is None:
        supported = ", ".join(sorted(_PROVIDERS.keys()))
        raise ValueError(f"Unsupported LLM provider: {name}. Supported providers: {supported}")
    return provider


def has_provider(name: str) -> bool:
    return name.strip().lower() in _PROVIDERS


def list_providers() -> list[str]:
    return sorted(_PROVIDERS.keys())
