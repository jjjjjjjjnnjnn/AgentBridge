"""Agent configuration and provider settings."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = Path.home() / ".relayos" / "config.yaml"

# Provider to environment variable mapping (used consistently across modules)
PROVIDER_ENV_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "ollama": "",  # no key required
}


def get_config_dir() -> Path:
    """Get config directory, respecting RELAYOS_CONFIG_DIR env var."""
    override = os.environ.get("RELAYOS_CONFIG_DIR")
    if override:
        return Path(override)
    return Path.home() / ".relayos"


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
class RelayOSConfig:
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    routing: RoutingPolicy = field(default_factory=RoutingPolicy)
    memory: dict = field(default_factory=lambda: {"type": "sqlite", "path": "~/.relayos/memory.db"})
    mcp_servers: dict[str, dict] = field(default_factory=dict)
    terminals: list[dict] = field(default_factory=list)  # terminal definitions
    mode: str = "auto"  # "auto" | "edit" — execution mode

    def resolve_api_key(self, provider: str) -> Optional[str]:
        cfg = self.providers.get(provider)
        if cfg and cfg.api_key:
            return cfg.api_key
        env_var = PROVIDER_ENV_MAP.get(provider)
        if env_var:
            return os.environ.get(env_var)
        return None


def load_config(path: Optional[Path] = None) -> RelayOSConfig:
    if not path:
        config_dir = get_config_dir()
        path = config_dir / "config.yaml"
    if not path.exists():
        logger.warning(f"Config not found at {path}. Run 'relayos init' to create one.")
        return RelayOSConfig()

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
    memory = raw.get("memory") or {"type": "sqlite", "path": "~/.relayos/memory.db"}
    terminals = raw.get("terminals") or []

    return RelayOSConfig(
        providers=providers,
        routing=routing,
        memory=memory,
        mcp_servers=mcp_servers,
        terminals=terminals,
        mode=raw.get("mode", "auto"),
    )
