"""ProviderRouter — weighted routing, auto/edit mode, fallback.

User config controls:
  - Weight: which providers get called more often
  - Mode: auto (no approval) vs edit (ask before each call)
  - Strategy: weighted | cheapest | fastest | quality
"""
from __future__ import annotations

import logging
import random
from typing import Optional

from relayos.providers import BaseProvider, ProviderDef, ProviderResult, create_provider, detect_providers

logger = logging.getLogger(__name__)


class ProviderRouter:
    """Routes tasks to providers based on weight, cost, and mode."""

    def __init__(self, providers: Optional[list[ProviderDef]] = None):
        self.providers = providers or detect_providers()
        self.mode: str = "auto"  # "auto" | "edit"

    def get_enabled(self) -> list[BaseProvider]:
        return [create_provider(p) for p in self.providers if p.enabled]

    def select(self, task_type: str = "", profile: str = "balanced") -> BaseProvider:
        """Select best provider for a task type.

        profile:
          - "free"       → prefer CLI (zero API cost)
          - "cheapest"   → lowest cost
          - "quality"    → best model (API only)
          - "balanced"/"weighted" → weighted random (default)
        """
        enabled = self.get_enabled()
        if not enabled:
            # Fallback: try any CLI provider
            cli = [p for p in enabled if isinstance(p, __import__("relayos.providers", fromlist=["CLIProvider"]).CLIProvider)]
            if cli:
                return cli[0]
            raise RuntimeError("No enabled providers. Configure API keys or install a CLI terminal.")

        if profile == "free":
            cli = [p for p in enabled if p.config.type == "cli"]
            if cli:
                return cli[0]

        if profile == "cheapest":
            return min(enabled, key=lambda p: p.estimate_cost(1000))

        if profile == "quality":
            # Prefer API with higher capability
            api = [p for p in enabled if p.config.type == "api"]
            if api:
                return api[0]
            return enabled[0]

        # Default: weighted random
        return self._weighted_random(enabled)

    def _weighted_random(self, providers: list[BaseProvider]) -> BaseProvider:
        weights = [max(p.config.weight, 1) for p in providers]
        return random.choices(providers, weights=weights)[0]

    def complete(self, prompt: str, task_type: str = "", profile: str = "",
                 on_confirm: Optional[callable] = None) -> ProviderResult:
        """Execute a prompt through the best provider.

        Args:
            prompt: The task/query text
            task_type: Optional task classification hint
            profile: Routing profile
            on_confirm: Callback for edit mode approval. Receives (provider_id, prompt)
                        and returns True to execute, False to skip.

        Returns:
            ProviderResult with the response
        """
        provider = self.select(task_type, profile)

        # Edit mode: ask for confirmation
        if self.mode == "edit" and on_confirm:
            if not on_confirm(provider.config.id, prompt):
                return ProviderResult(
                    content="", provider_id=provider.config.id,
                    error="Skipped (user declined)",
                )

        logger.info(f"[{provider.config.id}] starting...")
        result = provider.complete(prompt)
        logger.info(f"[{provider.config.id}] done ({result.duration_ms}ms)")
        return result

    def get_status(self) -> list[dict]:
        """Get human-readable status for all providers."""
        results = []
        for p in self.providers:
            inst = create_provider(p)
            results.append({
                "id": p.id,
                "name": p.display_name,
                "type": p.type,
                "model": p.model or p.binary,
                "weight": p.weight,
                "enabled": p.enabled,
                "available": inst.is_available(),
            })
        return results

    def set_mode(self, mode: str):
        """Set execution mode: auto or edit."""
        if mode in ("auto", "edit"):
            self.mode = mode

    def enable(self, provider_id: str, enabled: bool = True):
        for p in self.providers:
            if p.id == provider_id:
                p.enabled = enabled
                break

    def set_weight(self, provider_id: str, weight: int):
        for p in self.providers:
            if p.id == provider_id:
                p.weight = max(0, min(100, weight))
                break
