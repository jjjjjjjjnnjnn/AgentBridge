"""Flow Router — intelligent task dispatch engine.

Routes tasks to the optimal agent based on task type, cost policy,
and agent capability. Like a load balancer for AI models.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

# Default routing rules — task patterns → best provider
DEFAULT_RULES: dict[str, dict] = {
    "research": {
        "prompt_patterns": ["research", "analyze", "compare", "trend", "landscape", "competitor", "survey"],
        "provider": "google",
        "reason": "Gemini has free tier + 1M context for research",
    },
    "architecture": {
        "prompt_patterns": ["architecture", "design", "system", "structure", "schema", "blueprint"],
        "provider": "anthropic",
        "reason": "Claude excels at architecture and system design",
    },
    "coding": {
        "prompt_patterns": ["implement", "code", "function", "api", "endpoint", "class", "method"],
        "provider": "openai",
        "reason": "GPT-4o is strongest for code generation",
    },
    "review": {
        "prompt_patterns": ["review", "audit", "security", "vulnerability", "bug", "quality"],
        "provider": "deepseek",
        "reason": "DeepSeek has strong code analysis at lowest cost",
    },
    "planning": {
        "prompt_patterns": ["plan", "roadmap", "strategy", "priority", "milestone", "timeline"],
        "provider": "anthropic",
        "reason": "Claude excels at strategic planning",
    },
    "writing": {
        "prompt_patterns": ["write", "document", "readme", "draft", "essay", "article", "blog"],
        "provider": "openai",
        "reason": "GPT-4o produces natural writing",
    },
    "data": {
        "prompt_patterns": ["extract", "parse", "transform", "clean", "normalize", "json", "csv", "data"],
        "provider": "deepseek",
        "reason": "DeepSeek is cost-effective for data tasks",
    },
    "quick": {
        "prompt_patterns": ["summarize", "short", "quick", "brief", "tl;dr", "keywords"],
        "provider": "deepseek",
        "reason": "Use cheapest model for quick tasks",
    },
    "local": {
        "prompt_patterns": [],
        "provider": "ollama",
        "reason": "Local model for private/sensitive data",
    },
}


@dataclass
class RouteDecision:
    provider: str
    task_type: str
    confidence: float
    reason: str
    estimated_tokens: int = 0


class FlowRouter:
    """Routes tasks to optimal providers based on content analysis.

    Analyzes the prompt to determine task type, then selects the
    best provider based on routing rules and cost policy.
    """

    def __init__(self, rules_path: Optional[str] = None):
        self.rules = dict(DEFAULT_RULES)
        if rules_path:
            p = Path(rules_path)
            if p.exists():
                custom = yaml.safe_load(p.read_text(encoding="utf-8"))
                if custom:
                    self.rules.update(custom)

    def route(self, prompt: str, preferred: Optional[str] = None, policy: str = "balanced") -> RouteDecision:
        """Determine the best provider for a given prompt."""
        if preferred:
            return RouteDecision(
                provider=preferred,
                task_type="explicit",
                confidence=1.0,
                reason="User-specified provider",
                estimated_tokens=self._estimate_tokens(prompt),
            )

        prompt_lower = prompt.lower()
        best_match: tuple[str, str, float, str] = ("openai", "general", 0.0, "Default fallback")

        for task_type, rule in self.rules.items():
            patterns = rule.get("prompt_patterns", [])
            if not patterns:
                continue

            # Count matching patterns
            matches = sum(1 for p in patterns if p in prompt_lower)
            if matches == 0:
                continue

            confidence = matches / len(patterns)
            if confidence > best_match[2]:
                best_match = (rule["provider"], task_type, confidence, rule["reason"])

        provider, task_type, confidence, reason = best_match

        # Apply policy adjustments
        if policy == "cheapest" and provider != "ollama":
            # Bias toward cheaper alternatives
            cheap_order = {"ollama": 0, "deepseek": 0, "google": 0, "openai": 1, "anthropic": 2}
            current_rank = cheap_order.get(provider, 1)
            if current_rank > 0:
                provider = "deepseek" if "deepseek" in cheap_order else provider
                reason += " (policy: cheapest)"
        elif policy == "quality" and provider in ("deepseek", "ollama"):
            provider = "anthropic" if "anthropic" in DEFAULT_RULES else provider
            reason += " (policy: quality_first)"

        return RouteDecision(
            provider=provider,
            task_type=task_type,
            confidence=confidence,
            reason=reason,
            estimated_tokens=self._estimate_tokens(prompt),
        )

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimation (4 chars per token)."""
        return len(text) // 4

    def classify(self, prompt: str) -> str:
        """Quick classification without full routing."""
        return self.route(prompt).task_type


