"""BudgetGuard — cost control with hard limits.

Prevents bill shock by checking:
  - per_task_usd: single task cost threshold
  - daily_usd: daily cumulative spend limit
  - monthly_usd: monthly cumulative spend limit

All checks happen BEFORE execution.
"""
from __future__ import annotations

import logging
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class GuardResult:
    action: str      # "allow" | "confirm" | "block"
    message: str = ""


@dataclass
class BudgetLimits:
    per_task_usd: float = 0.05
    daily_usd: float = 1.00
    monthly_usd: float = 10.00
    warn_at_percent: int = 80


class BudgetGuard:
    """Checks cost limits before executing tasks.

    Integrates with CostManager for spend tracking.
    """

    def __init__(self, limits: Optional[BudgetLimits] = None, db_path: str = "~/.relayos/cost.db"):
        self.limits = limits or BudgetLimits()
        self._db_path = str(Path(db_path).expanduser())

    def _today_range(self) -> tuple[str, str]:
        """Get ISO timestamps for start/end of today."""
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end = now.isoformat()
        return start, end

    def _month_range(self) -> tuple[str, str]:
        """Get ISO timestamps for start/end of this month."""
        now = datetime.now(timezone.utc)
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        end = now.isoformat()
        return start, end

    def _sum_costs(self, start: str, end: str) -> float:
        """Sum costs in the time range."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                row = conn.execute(
                    "SELECT COALESCE(SUM(cost), 0) as total FROM usage WHERE timestamp >= ? AND timestamp <= ?",
                    (start, end),
                ).fetchone()
                return row[0] if row else 0.0
        except Exception:
            return 0.0

    def check(self, estimated_cost: float) -> GuardResult:
        """Check if a task with estimated_cost should proceed.

        Returns:
            GuardResult with action="allow", "confirm", or "block"
        """
        # 1. Per-task check
        if estimated_cost > self.limits.per_task_usd:
            return GuardResult(
                action="confirm",
                message=f"Estimated cost ${estimated_cost:.3f} exceeds per-task limit ${self.limits.per_task_usd:.2f}. Confirm?",
            )

        # 2. Daily check
        start, end = self._today_range()
        today_spent = self._sum_costs(start, end)
        if today_spent + estimated_cost > self.limits.daily_usd:
            return GuardResult(
                action="block",
                message=f"Daily spend ${today_spent:.3f} + estimated ${estimated_cost:.3f} exceeds daily limit ${self.limits.daily_usd:.2f}",
            )

        # 3. Warn at percentage
        if today_spent > 0:
            pct = (today_spent / self.limits.daily_usd) * 100
            if pct >= self.limits.warn_at_percent:
                logger.info(f"Daily spend at {pct:.0f}% of limit (${today_spent:.3f}/${self.limits.daily_usd:.2f})")

        return GuardResult(action="allow")

    def get_today_spend(self) -> float:
        """Get today's total spend."""
        return self._sum_costs(*self._today_range())

    def get_monthly_spend(self) -> float:
        """Get this month's total spend."""
        return self._sum_costs(*self._month_range())

    def get_status(self) -> dict:
        """Get full budget status for display."""
        today = self.get_today_spend()
        monthly = self.get_monthly_spend()
        return {
            "today": round(today, 4),
            "daily_limit": self.limits.daily_usd,
            "daily_pct": round((today / self.limits.daily_usd) * 100, 1) if self.limits.daily_usd > 0 else 0,
            "monthly": round(monthly, 4),
            "monthly_limit": self.limits.monthly_usd,
            "monthly_pct": round((monthly / self.limits.monthly_usd) * 100, 1) if self.limits.monthly_usd > 0 else 0,
            "per_task_limit": self.limits.per_task_usd,
        }
