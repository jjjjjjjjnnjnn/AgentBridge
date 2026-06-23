"""Adapter registry — discover adapters via entry_points or manual register."""
from __future__ import annotations

from typing import Any

from agentmesh.adapters.base import BaseAdapter

_REGISTRY: dict[str, type[BaseAdapter]] = {}


def register(name: str, cls: type[BaseAdapter]):
    _REGISTRY[name] = cls


def get_adapter(name: str, config: dict[str, Any] | None = None) -> BaseAdapter:
    cls = _REGISTRY.get(name)
    if not cls:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown adapter '{name}'. Available: {available}")
    return cls(config)


def list_adapters() -> list[str]:
    return sorted(_REGISTRY)


# Late imports to avoid circular deps
from agentmesh.adapters.openai import OpenAIAdapter  # noqa: E402
from agentmesh.adapters.anthropic import AnthropicAdapter  # noqa: E402
from agentmesh.adapters.google import GoogleAdapter  # noqa: E402
from agentmesh.adapters.ollama import OllamaAdapter  # noqa: E402
from agentmesh.adapters.deepseek import DeepSeekAdapter  # noqa: E402

register("openai", OpenAIAdapter)
register("anthropic", AnthropicAdapter)
register("google", GoogleAdapter)
register("ollama", OllamaAdapter)
register("deepseek", DeepSeekAdapter)
