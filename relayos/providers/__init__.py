"""Unified Provider abstraction — hides CLI vs API behind one interface.

A Provider is anything that can complete a prompt:
  - APIProvider: calls OpenAI/Anthropic/Google/DeepSeek/Ollama API
  - CLIProvider: calls local CLI terminal (claude, opencode, mimo, etc.)

User sees only "providers", not "CLI vs API".
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProviderResult:
    content: str
    provider_id: str
    model: str = ""
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    duration_ms: int = 0
    error: Optional[str] = None


@dataclass
class ProviderDef:
    """User-facing provider configuration."""
    id: str                     # e.g. "claude-api", "opencode-local"
    type: str                   # "api" or "cli"
    display_name: str           # e.g. "Claude Sonnet"
    provider: str               # e.g. "anthropic", "opencode"
    model: str = ""             # e.g. "claude-sonnet-4-6"
    binary: str = ""            # CLI binary name (for cli type)
    weight: int = 100           # 0-100, routing weight
    enabled: bool = True
    api_key: str = ""           # encrypted/empty
    base_url: str = ""
    priority: int = 0           # lower = preferred


class BaseProvider(ABC):
    """Abstract interface for all providers (API + CLI)."""

    def __init__(self, config: ProviderDef):
        self.config = config

    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> ProviderResult:
        ...

    def estimate_cost(self, chars: int = 1000) -> float:
        return 0.0  # override in subclasses

    @abstractmethod
    def is_available(self) -> bool:
        ...


class APIProvider(BaseProvider):
    """Provider that calls a remote API (OpenAI, Anthropic, etc.)."""

    def complete(self, prompt: str, **kwargs) -> ProviderResult:
        from relayos.adapters import get_adapter
        cfg = self.config
        adapter = get_adapter(cfg.provider, {
            "api_key": cfg.api_key,
            "model": cfg.model or "",
            "base_url": cfg.base_url or "",
        })
        start = time.time()
        response = adapter.chat(prompt, **kwargs)
        dur = int((time.time() - start) * 1000)
        usage = response.usage or {}
        return ProviderResult(
            content=response.content,
            provider_id=cfg.id,
            model=response.model,
            tokens_in=usage.get("input_tokens", usage.get("prompt_tokens", 0)),
            tokens_out=usage.get("output_tokens", usage.get("completion_tokens", 0)),
            duration_ms=dur,
        )

    def estimate_cost(self, chars: int = 1000) -> float:
        """Rough cost estimate based on provider/model."""
        costs = {
            "gpt-4o": (0.0025, 0.01),
            "gpt-4o-mini": (0.00015, 0.0006),
            "claude-sonnet-4-20250514": (0.003, 0.015),
            "claude-haiku-4-20251001": (0.001, 0.005),
            "gemini-2.5-flash": (0.0, 0.0),
            "deepseek-chat": (0.00014, 0.00028),
        }
        tokens = chars // 4
        inp, out = costs.get(self.config.model, (0.001, 0.002))
        return round((tokens / 1000) * inp + (tokens / 1000) * out, 6)

    def is_available(self) -> bool:
        return bool(self.config.api_key)


class CLIProvider(BaseProvider):
    """Provider that calls a local CLI terminal (claude, opencode, etc.)."""

    def complete(self, prompt: str, **kwargs) -> ProviderResult:
        cfg = self.config
        binary = cfg.binary or cfg.provider
        if not shutil.which(binary):
            return ProviderResult(
                content="", provider_id=cfg.id,
                error=f"CLI '{binary}' not found. Install it first.",
            )

        # Build command args
        cmd = [binary]
        typed_cmds = {
            "claude": ["-p", prompt],
            "opencode": ["-p", prompt],
            "mimo": ["-p", prompt],
            "codex": ["-p", prompt],
            "qcode": ["--prompt", prompt],
        }
        args = typed_cmds.get(cfg.provider, ["--prompt", prompt])
        cmd.extend(args)

        start = time.time()
        try:
            result = subprocess.run(
                cmd, input=prompt if "{stdin}" in str(cmd) else None,
                capture_output=True, text=True, timeout=300,
            )
            dur = int((time.time() - start) * 1000)
            if result.returncode != 0:
                return ProviderResult(
                    content=result.stderr[:500], provider_id=cfg.id,
                    error=result.stderr[:200], duration_ms=dur,
                )
            return ProviderResult(
                content=result.stdout.strip(),
                provider_id=cfg.id,
                model=cfg.model or cfg.provider,
                duration_ms=dur,
            )
        except subprocess.TimeoutExpired:
            return ProviderResult(
                content="", provider_id=cfg.id,
                error="CLI timed out (300s)", duration_ms=300000,
            )
        except Exception as e:
            return ProviderResult(
                content="", provider_id=cfg.id,
                error=str(e),
            )

    def estimate_cost(self, chars: int = 1000) -> float:
        return 0.0  # CLI costs are sunk (user already pays subscription)

    def is_available(self) -> bool:
        return shutil.which(self.config.binary or self.config.provider) is not None


# ── Factory ────────────────────────────────────────────────────

def create_provider(config: ProviderDef) -> BaseProvider:
    """Create a provider from a ProviderDef config."""
    if config.type == "cli":
        return CLIProvider(config)
    return APIProvider(config)


def detect_providers() -> list[ProviderDef]:
    """Auto-detect available providers (CLI + API keys)."""
    import os
    detected = []

    # 1. API providers with env keys
    api_providers = {
        "openai": ("OpenAI GPT-4o", "gpt-4o"),
        "anthropic": ("Claude Sonnet", "claude-sonnet-4-20250514"),
        "google": ("Gemini Flash", "gemini-2.5-flash"),
        "deepseek": ("DeepSeek Chat", "deepseek-chat"),
    }
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GEMINI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    for prov, (name, model) in api_providers.items():
        key = os.environ.get(env_map[prov], "")
        detected.append(ProviderDef(
            id=f"{prov}-api",
            type="api",
            display_name=name,
            provider=prov,
            model=model,
            api_key=key or "",
            weight=80 if key else 0,
            enabled=bool(key),
            priority=0 if key else 99,
        ))

    # 2. CLI terminals (auto-detected)
    cli_terminals = [
        ("claude", "Claude Code CLI"),
        ("opencode", "OpenCode CLI"),
        ("mimo", "Mimo CLI"),
        ("codex", "Codex CLI"),
    ]
    for binary, label in cli_terminals:
        detected.append(ProviderDef(
            id=f"{binary}-cli",
            type="cli",
            display_name=label,
            provider=binary,
            binary=binary,
            weight=50,
            enabled=shutil.which(binary) is not None,
            priority=0 if shutil.which(binary) else 99,
        ))

    return detected
