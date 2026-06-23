"""Capability Registry — model capability scores for every task type.

Each model has a score (1-10) for each capability:
- coding
- architecture
- review
- research
- reasoning
- quick
- writing

Used by the Model Scheduler to select the optimal model for each task.
"""
from __future__ import annotations

from typing import Optional

# Model → capability scores (1-10, 10 = best)
CAPABILITY_SCORES: dict[str, dict[str, int]] = {
    # ── Anthropic ────────────────────────────────────────
    "claude-sonnet-4-20250514": {
        "coding": 9, "architecture": 10, "review": 8, "research": 7,
        "reasoning": 10, "quick": 5, "writing": 8,
    },
    "claude-haiku-4-20251001": {
        "coding": 6, "architecture": 5, "review": 5, "research": 5,
        "reasoning": 5, "quick": 9, "writing": 6,
    },
    "claude-opus-4-20250514": {
        "coding": 10, "architecture": 10, "review": 9, "research": 8,
        "reasoning": 10, "quick": 3, "writing": 9,
    },
    # ── OpenAI ───────────────────────────────────────────
    "gpt-4o": {
        "coding": 9, "architecture": 8, "review": 7, "research": 7,
        "reasoning": 8, "quick": 6, "writing": 9,
    },
    "gpt-4o-mini": {
        "coding": 7, "architecture": 5, "review": 6, "research": 5,
        "reasoning": 5, "quick": 10, "writing": 7,
    },
    "o3-mini": {
        "coding": 8, "architecture": 7, "review": 8, "research": 6,
        "reasoning": 10, "quick": 4, "writing": 5,
    },
    # ── Google ───────────────────────────────────────────
    "gemini-2.5-flash": {
        "coding": 7, "architecture": 6, "review": 6, "research": 9,
        "reasoning": 6, "quick": 9, "writing": 7,
    },
    "gemini-2.5-pro": {
        "coding": 8, "architecture": 8, "review": 7, "research": 9,
        "reasoning": 8, "quick": 5, "writing": 8,
    },
    # ── DeepSeek ─────────────────────────────────────────
    "deepseek-chat": {
        "coding": 8, "architecture": 7, "review": 8, "research": 6,
        "reasoning": 7, "quick": 9, "writing": 6,
    },
    "deepseek-reasoner": {
        "coding": 7, "architecture": 6, "review": 7, "research": 5,
        "reasoning": 9, "quick": 3, "writing": 5,
    },
    # ── Ollama (local) ───────────────────────────────────
    "qwen2.5:7b": {
        "coding": 6, "architecture": 4, "review": 5, "research": 4,
        "reasoning": 4, "quick": 8, "writing": 5,
    },
    "qwen2.5:32b": {
        "coding": 7, "architecture": 6, "review": 6, "research": 5,
        "reasoning": 6, "quick": 5, "writing": 6,
    },
    "llama3.1:8b": {
        "coding": 5, "architecture": 4, "review": 4, "research": 4,
        "reasoning": 4, "quick": 7, "writing": 5,
    },
    "codellama:7b": {
        "coding": 7, "architecture": 3, "review": 5, "research": 2,
        "reasoning": 3, "quick": 6, "writing": 3,
    },
    "mistral:7b": {
        "coding": 5, "architecture": 4, "review": 4, "research": 4,
        "reasoning": 4, "quick": 7, "writing": 5,
    },
}

# Terminal CLI → capability scores (for CLI-based workers like opencode, mimo)
TERMINAL_CAPABILITIES: dict[str, dict[str, int]] = {
    "opencode": {"coding": 7, "architecture": 5, "review": 6, "research": 5, "reasoning": 5, "quick": 8, "writing": 5},
    "mimo": {"coding": 6, "architecture": 4, "review": 5, "research": 4, "reasoning": 4, "quick": 9, "writing": 5},
    "claude": {"coding": 9, "architecture": 9, "review": 8, "research": 7, "reasoning": 9, "quick": 5, "writing": 8},
}

# Model cost tiers (estimated USD per 1K tokens output)
MODEL_COST_TIER: dict[str, str] = {
    "free": ["qwen2.5:7b", "qwen2.5:32b", "llama3.1:8b", "codellama:7b", "mistral:7b"],
    "cheap": ["deepseek-chat", "deepseek-reasoner", "gemini-2.5-flash"],
    "moderate": ["gpt-4o-mini", "gemini-2.5-pro", "claude-haiku-4-20251001"],
    "expensive": ["gpt-4o", "claude-sonnet-4-20250514", "o3-mini"],
    "premium": ["claude-opus-4-20250514"],
}

# Provider → default model (for when model is not specified)
PROVIDER_DEFAULT_MODEL: dict[str, str] = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "google": "gemini-2.5-flash",
    "deepseek": "deepseek-chat",
    "ollama": "qwen2.5:7b",
}


def get_capability(model: str, capability: str) -> int:
    """Get capability score for a model on a specific task type."""
    model_scores = CAPABILITY_SCORES.get(model, {})
    return model_scores.get(capability, 5)  # default to 5 (mid)


def get_best_model(capability: str, top_n: int = 3) -> list[tuple[str, int]]:
    """Get the top N models for a given capability."""
    scored = []
    for model, scores in CAPABILITY_SCORES.items():
        score = scores.get(capability, 0)
        if score > 0:
            scored.append((model, score))
    scored.sort(key=lambda x: -x[1])
    return scored[:top_n]


def get_cost_tier(model: str) -> str:
    """Get the cost tier for a model."""
    for tier, models in MODEL_COST_TIER.items():
        if model in models:
            return tier
    return "moderate"


def score_models(capability: str, cost_weight: float = 0.3,
                 capability_weight: float = 0.7) -> list[dict]:
    """Score models by combined capability and cost."""
    results = []
    tier_weights = {"free": 1.0, "cheap": 0.8, "moderate": 0.5, "expensive": 0.3, "premium": 0.1}

    for model, scores in CAPABILITY_SCORES.items():
        cap_score = scores.get(capability, 0)
        cost_tier = get_cost_tier(model)
        cost_score = tier_weights.get(cost_tier, 0.5)

        combined = (cap_score / 10) * capability_weight + cost_score * cost_weight
        results.append({
            "model": model,
            "capability_score": cap_score,
            "cost_tier": cost_tier,
            "cost_score": cost_score,
            "combined": round(combined, 3),
        })

    results.sort(key=lambda x: -x["combined"])
    return results
