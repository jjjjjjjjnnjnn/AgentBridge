"""Adapter registry — discover adapters via entry_points or manual register."""
from __future__ import annotations

import logging
from typing import Any

from relayos.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, type[BaseAdapter]] = {}


def register(name: str, cls: type[BaseAdapter]):
    _REGISTRY[name] = cls


def _discover_entry_points():
    """Discover adapters registered via pyproject.toml entry points."""
    try:
        from importlib.metadata import entry_points
        eps = entry_points(group="relayos.adapters")
        for ep in eps:
            if ep.name not in _REGISTRY:
                try:
                    cls = ep.load()
                    _REGISTRY[ep.name] = cls
                    logger.debug(f"Discovered adapter '{ep.name}' via entry point")
                except Exception as e:
                    logger.warning(f"Failed to load adapter '{ep.name}': {e}")
    except Exception:
        pass  # entry point discovery is best-effort


# Discover entry points on import
_discover_entry_points()


def get_adapter(name: str, config: dict[str, Any] | None = None) -> BaseAdapter:
    cls = _REGISTRY.get(name)
    if not cls:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return cls(config)


def list_adapters() -> list[str]:
    return sorted(_REGISTRY)


# Late imports to avoid circular deps
from relayos.adapters.openai import OpenAIAdapter  # noqa: E402
from relayos.adapters.anthropic import AnthropicAdapter  # noqa: E402
from relayos.adapters.google import GoogleAdapter  # noqa: E402
from relayos.adapters.ollama import OllamaAdapter  # noqa: E402
from relayos.adapters.deepseek import DeepSeekAdapter  # noqa: E402

register("openai", OpenAIAdapter)
register("anthropic", AnthropicAdapter)
register("google", GoogleAdapter)
register("ollama", OllamaAdapter)
register("deepseek", DeepSeekAdapter)
