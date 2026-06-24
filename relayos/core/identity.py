"""Worker Identity — makes each worker feel like a real team member.

Each worker has:
- Identity: role, responsibilities, emoji, description
- Decisions: log of technical decisions made
- Project state: current project context
- Memory summary: compressed view of what the worker knows
"""
from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


@dataclass
class WorkerIdentity:
    name: str
    role: str
    emoji: str = "🤖"
    description: str = ""
    responsibilities: list[str] = field(default_factory=list)
    project: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Decision:
    id: int = 0
    worker: str = ""
    title: str = ""
    decision: str = ""
    reasoning: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class IdentityStore:
    """Persistent identity storage for workers — decisions, project state, facts."""

    def __init__(self, db_path: str = "~/.relayos/identity.db"):
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
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker TEXT NOT NULL,
                    title TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    reasoning TEXT DEFAULT '',
                    timestamp TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS project_state (
                    worker TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (worker, key)
                )
            """)
            conn.commit()

    # ── Decisions ──────────────────────────────────────────

    def add_decision(self, worker: str, title: str, decision: str, reasoning: str = "") -> int:
        ts = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "INSERT INTO decisions (worker, title, decision, reasoning, timestamp) VALUES (?, ?, ?, ?, ?)",
            (worker, title, decision, reasoning, ts),
        )
        self._conn.commit()
        return cur.lastrowid or 0

    def get_decisions(self, worker: str, limit: int = 10) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM decisions WHERE worker = ? ORDER BY timestamp DESC LIMIT ?",
            (worker, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Project State ──────────────────────────────────────

    def set_state(self, worker: str, key: str, value: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO project_state (worker, key, value) VALUES (?, ?, ?)",
            (worker, key, value),
        )
        self._conn.commit()

    def get_state(self, worker: str) -> dict[str, str]:
        rows = self._conn.execute(
            "SELECT key, value FROM project_state WHERE worker = ?", (worker,)
        ).fetchall()
        return {r["key"]: r["value"] for r in rows}

    # ── Summary ────────────────────────────────────────────

    def get_summary(self, worker: str) -> str:
        """Generate a compressed worker summary (200-500 tokens)."""
        parts = [f"=== {worker} ==="]
        state = self.get_state(worker)
        if state:
            parts.append("Project state:")
            for k, v in state.items():
                parts.append(f"  {k}: {v[:80]}")

        decisions = self.get_decisions(worker, limit=5)
        if decisions:
            parts.append("Recent decisions:")
            for d in decisions:
                parts.append(f"  - {d['title']}: {d['decision'][:100]}")

        result = "\n".join(parts)
        # Keep under ~2000 chars (~500 tokens)
        if len(result) > 2000:
            result = result[:2000] + "\n... [truncated]"
        return result
