"""Cost Manager — tracks usage and routes by policy.

Policies:
  free_first   → try free/cheap models first, fall back to paid
  quality_first → use best model regardless of cost
  cheapest     → always use the cheapest available
"""
from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Approximate cost per 1K tokens (USD)
PROVIDER_COSTS: dict[str, dict[str, float]] = {
    "openai": {"input": 0.0025, "output": 0.01},
    "anthropic": {"input": 0.003, "output": 0.015},
    "google": {"input": 0.000, "output": 0.000},  # free tier
    "deepseek": {"input": 0.00014, "output": 0.00028},
    "ollama": {"input": 0.0, "output": 0.0},  # local, free
}

# Free/cheap provider ordering
FREE_FIRST_ORDER = ["ollama", "google", "deepseek", "openai", "anthropic"]
QUALITY_FIRST_ORDER = ["anthropic", "openai", "google", "deepseek", "ollama"]
CHEAPEST_ORDER = ["ollama", "deepseek", "google", "openai", "anthropic"]


@dataclass
class UsageRecord:
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CostManager:
    """Tracks API usage and cost across all providers."""

    def __init__(self, db_path: str = "~/.relayos/cost.db"):
        self._db_path = str(Path(db_path).expanduser())
        self._local = threading.local()
        self._init_db()

    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _init_db(self):
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def track(self, provider: str, model: str, input_tokens: int = 0, output_tokens: int = 0):
        """Record a usage event."""
        costs = PROVIDER_COSTS.get(provider, {"input": 0, "output": 0})
        cost = (input_tokens / 1000) * costs.get("input", 0) + (output_tokens / 1000) * costs.get("output", 0)
        ts = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO usage (provider, model, input_tokens, output_tokens, cost, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (provider, model, input_tokens, output_tokens, cost, ts),
        )
        self._conn.commit()

    def get_report(self) -> dict:
        """Get aggregate usage report."""
        rows = self._conn.execute(
            "SELECT provider, COUNT(*) as calls, SUM(input_tokens) as input, SUM(output_tokens) as output, SUM(cost) as total_cost FROM usage GROUP BY provider ORDER BY total_cost DESC"
        ).fetchall()
        providers = {}
        total_cost = 0.0
        total_calls = 0
        for r in rows:
            providers[r["provider"]] = {
                "calls": r["calls"],
                "input_tokens": r["input"] or 0,
                "output_tokens": r["output"] or 0,
                "cost": round(r["total_cost"] or 0, 6),
            }
            total_cost += r["total_cost"] or 0
            total_calls += r["calls"]
        return {
            "total_calls": total_calls,
            "total_cost": round(total_cost, 6),
            "providers": providers,
        }

    def get_summary(self) -> str:
        """Get a human-readable usage summary."""
        r = self.get_report()
        lines = [f"Total API calls: {r['total_calls']}", f"Total cost: ${r['total_cost']:.4f}"]
        for pname, pdata in r.get("providers", {}).items():
            lines.append(f"  {pname}: {pdata['calls']} calls, {pdata['input_tokens']} in / {pdata['output_tokens']} out, ${pdata['cost']:.4f}")
        return "\n".join(lines) if len(r.get("providers", {})) else "No usage recorded yet."

    def select_provider(self, preferred: str | None = None, policy: str = "balanced",
                        available_providers: Optional[list[str]] = None) -> str:
        """Select the best provider based on policy and availability.

        Args:
            preferred: If set, returns this provider (no checking)
            policy: Routing policy string
            available_providers: List of configured/available providers.
                If None, returns the policy default without checking.
        """
        if preferred:
            return preferred

        order = {
            "free_first": FREE_FIRST_ORDER,
            "quality": QUALITY_FIRST_ORDER,
            "cheapest": CHEAPEST_ORDER,
        }.get(policy, [])

        if not order:
            return "openai"

        if available_providers:
            for provider in order:
                if provider in available_providers:
                    return provider
            return order[0]  # none available, return first anyway

        return order[0]
