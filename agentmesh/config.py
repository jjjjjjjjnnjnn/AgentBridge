"""Agent configuration and provider settings."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

DEFAULT_CONFIG_PATH = Path.home() / ".agentmesh" / "config.yaml"


@dataclass
class ProviderConfig:
    api_key: Optional[str] = None
    model: str = ""
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class RoutingPolicy:
    default: str = "balanced"
    policies: dict[str, str] = field(default_factory=dict)


@dataclass
class AgentMeshConfig:
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    routing: RoutingPolicy = field(default_factory=RoutingPolicy)
    memory: dict = field(default_factory=lambda: {"type": "sqlite", "path": "~/.agentmesh/memory.db"})
    mcp_servers: dict[str, dict] = field(default_factory=dict)

    def resolve_api_key(self, provider: str) -> Optional[str]:
        cfg = self.providers.get(provider)
        if cfg and cfg.api_key:
            return cfg.api_key

        env_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }
        return os.environ.get(env_map.get(provider, ""))


def load_config(path: Optional[Path] = None) -> AgentMeshConfig:
    path = path or DEFAULT_CONFIG_PATH
    if not path.exists():
        return AgentMeshConfig()

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    providers = {}
    for name, p in (raw.get("providers") or {}).items():
        providers[name] = ProviderConfig(
            api_key=p.get("api_key"),
            model=p.get("model", ""),
            base_url=p.get("base_url"),
            max_tokens=p.get("max_tokens", 4096),
            temperature=p.get("temperature", 0.7),
        )

    routing_raw = raw.get("routing", {})
    routing = RoutingPolicy(
        default=routing_raw.get("default", "balanced"),
        policies=routing_raw.get("policies", {}),
    )

    mcp_servers = raw.get("mcp_servers") or {}
    memory = raw.get("memory") or {"type": "sqlite", "path": "~/.agentmesh/memory.db"}

    return AgentMeshConfig(
        providers=providers,
        routing=routing,
        memory=memory,
        mcp_servers=mcp_servers,
    )
