"""Model Scheduler — cost-aware, capability-based, escalation routing.

Routes tasks to optimal models based on:
1. Task type → best capability match
2. User profile → cost preference (free/balanced/quality)
3. Escalation → auto-upgrade if confidence < threshold

Like a CPU scheduler, but for AI models.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Optional

from relayos.core.capabilities import (
    CAPABILITY_SCORES,
    PROVIDER_DEFAULT_MODEL,
    get_cost_tier,
    score_models,
)
from relayos.core.provider_registry import PROVIDERS

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.6  # auto-escalate if confidence below this


@dataclass
class RouteVerdict:
    model: str
    provider: str
    capability_score: int
    cost_tier: str
    estimated_cost: float  # USD
    confidence: float
    candidate_chain: list[str]  # models considered (primary + fallbacks)
    reason: str


class ModelScheduler:
    """Cost-aware, capability-based model router with escalation.

    Usage:
        scheduler = ModelScheduler()
        verdict = scheduler.route("Implement JWT auth", "coding", "free")
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}

    def classify_task(self, prompt: str) -> str:
        """Classify a prompt into a task type based on content keywords."""
        prompt_lower = prompt.lower()

        type_patterns = {
            "architecture": ["architecture", "design", "system", "structure", "schema", "blueprint", "plan",
                             "component", "module", "data flow", "tech stack", "scalab"],
            "review": ["code review", "audit", "vulnerability", "security review", "quality",
                       "correctness", "bugs", "code quality", "static analysis", "lint",
                       "review this", "review the"],
            "research": ["research", "analyze", "compare", "trend", "landscape", "competitor", "survey",
                         "literature", "study", "investigate", "what is", "explain"],
            "reasoning": ["reason", "think", "logic", "solve", "problem", "math", "puzzle",
                          "inference", "deduce", "derive", "proof", "calculate"],
            "quick": ["summarize", "short", "quick", "brief", "tl;dr", "keywords", "summar",
                      "explain briefly", "in short", "concise"],
            "writing": ["write", "document", "readme", "draft", "essay", "article", "blog", "doc",
                        "tutorial", "guide", "documentation", "composition"],
            "coding": ["implement", "code", "function", "api", "endpoint", "class", "method",
                       "debug", "fix", "test", "refactor", "jwt", "auth", "database", "sql",
                       "program", "script", "algorithm", "library", "framework", "build",
                       "create", "add feature", "error handling"],
        }

        best_type = "coding"
        best_count = 0

        for task_type, patterns in type_patterns.items():
            count = sum(1 for p in patterns if p in prompt_lower)
            # Boost review when "review" appears as the very first word
            if task_type == "review" and prompt_lower.startswith("review"):
                count += 1
            if count > best_count:
                best_count = count
                best_type = task_type

        return best_type

    def estimate_cost(self, model: str, input_chars: int = 1000, output_chars: int = 2000) -> float:
        """Estimate cost for a model call (rough)."""
        provider_info = None
        for p in PROVIDERS.values():
            for m in p.models:
                if m.id == model:
                    provider_info = m
                    break
            if provider_info:
                break

        if not provider_info:
            return 0.0

        input_tokens = input_chars // 4
        output_tokens = output_chars // 4

        cost = (input_tokens / 1000) * provider_info.cost_per_1k_input
        cost += (output_tokens / 1000) * provider_info.cost_per_1k_output
        return round(cost, 6)

    def route(self, prompt: str, task_type: Optional[str] = None,
              profile: str = "balanced") -> RouteVerdict:
        """Route a task to the optimal model based on type and profile.

        Args:
            prompt: The task prompt
            task_type: Explicit task type (auto-classified if None)
            profile: User profile - "free", "balanced", or "quality"

        Returns:
            RouteVerdict with the selected model and routing info
        """
        if not task_type:
            task_type = self.classify_task(prompt)

        # Score all models for this task type
        scored = score_models(task_type)

        # Apply profile-based filtering
        if profile == "free":
            # Prefer free models, escalate to cheap if none qualify
            candidates = [s for s in scored if s["cost_tier"] == "free"]
            if not candidates:
                candidates = [s for s in scored if s["cost_tier"] in ("free", "cheap")]
        elif profile == "quality":
            # Prefer highest capability regardless of cost
            candidates = sorted(scored, key=lambda x: -x["capability_score"])
        else:
            # Balanced: prefer combined score
            candidates = scored

        if not candidates:
            candidates = scored  # fallback

        best = candidates[0]
        model = best["model"]
        provider = self._model_to_provider(model)

        # Calculate estimated cost
        est_cost = self.estimate_cost(model)
        confidence = min(best["capability_score"] / 10, 1.0)

        # Build candidate chain (models considered, in order)
        chain = [model]
        if confidence < CONFIDENCE_THRESHOLD and len(candidates) > 1:
            # Escalate to next best
            next_best = candidates[1]
            chain.append(next_best["model"])

        return RouteVerdict(
            model=model,
            provider=provider,
            capability_score=best["capability_score"],
            cost_tier=best["cost_tier"],
            estimated_cost=est_cost,
            confidence=round(confidence, 2),
            candidate_chain=chain,
            reason=f"{task_type} → {model} ({best['cost_tier']}, score={best['capability_score']})",
        )

    def estimate(self, prompt: str, task_type: Optional[str] = None) -> dict:
        """Show cost estimates for all profiles."""
        results = {}
        for profile in ("free", "balanced", "quality"):
            v = self.route(prompt, task_type, profile)
            results[profile] = {
                "model": v.model,
                "provider": v.provider,
                "cost_tier": v.cost_tier,
                "estimated_cost": v.estimated_cost,
                "confidence": v.confidence,
                "reason": v.reason,
            }
        return results

    def _model_to_provider(self, model: str) -> str:
        for provider, default in PROVIDER_DEFAULT_MODEL.items():
            if default == model:
                return provider
        # Fallback: look up by prefix
        model_lower = model.lower()
        if "claude" in model_lower:
            return "anthropic"
        if "gpt" in model_lower or "o3" in model_lower:
            return "openai"
        if "gemini" in model_lower:
            return "google"
        if "deepseek" in model_lower:
            return "deepseek"
        if "qwen" in model_lower or "llama" in model_lower or "codellama" in model_lower or "mistral" in model_lower:
            return "ollama"
        return "openai"
