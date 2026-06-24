"""State Store — unified SQLite state layer for RelayOS.

Four core tables replace chat history:
1. workers     — Worker identity (permanent)
2. state       — Project-level key-value facts
3. decisions   — Append-only decision log
4. events      — Append-only event log (event sourcing)
5. tasks       — Worker-to-worker task passing (not messages)

No chat history. No conversation logs. Only structured state.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _uuid() -> str:
    return f"task-{uuid.uuid4().hex[:12]}"


class StateStore:
    """Unified state layer. All data in ~/.relayos/state.db."""

    def __init__(self, db_path: str = "~/.relayos/state.db"):
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
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS workers (
                    id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    provider TEXT NOT NULL DEFAULT '',
                    model TEXT NOT NULL DEFAULT '',
                    constraints TEXT DEFAULT '[]',
                    task_count INTEGER DEFAULT 0,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_by TEXT,
                    updated_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    worker_id TEXT,
                    summary TEXT NOT NULL,
                    reason TEXT DEFAULT '',
                    category TEXT DEFAULT 'general',
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    worker_id TEXT,
                    task_id TEXT,
                    payload TEXT DEFAULT '{}',
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    from_worker TEXT NOT NULL,
                    to_worker TEXT NOT NULL,
                    task_type TEXT NOT NULL DEFAULT 'request',
                    payload TEXT NOT NULL DEFAULT '{}',
                    status TEXT NOT NULL DEFAULT 'pending',
                    parent_task_id TEXT,
                    created_at INTEGER NOT NULL,
                    resolved_at INTEGER
                );

                CREATE INDEX IF NOT EXISTS idx_tasks_inbox ON tasks(to_worker, status);
                CREATE INDEX IF NOT EXISTS idx_decisions_worker ON decisions(worker_id);
                CREATE INDEX IF NOT EXISTS idx_events_time ON events(created_at);
                CREATE INDEX IF NOT EXISTS idx_state_worker ON state(updated_by);
            """)
            conn.commit()

    # ── Workers ────────────────────────────────────────────

    def upsert_worker(self, wid: str, role: str, provider: str = "", model: str = "", constraints: list | None = None):
        now = _ts()
        self._conn.execute(
            "INSERT INTO workers (id, role, provider, model, constraints, task_count, created_at) "
            "VALUES (?, ?, ?, ?, ?, COALESCE((SELECT task_count FROM workers WHERE id=?), 0), COALESCE((SELECT created_at FROM workers WHERE id=?), ?)) "
            "ON CONFLICT(id) DO UPDATE SET role=excluded.role, provider=excluded.provider, model=excluded.model, constraints=excluded.constraints",
            (wid, role, provider, model, json.dumps(constraints or []), wid, wid, now),
        )
        self._conn.commit()

    def get_worker(self, wid: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM workers WHERE id=?", (wid,)).fetchone()
        if row:
            d = dict(row)
            d["constraints"] = json.loads(d.get("constraints", "[]"))
            return d
        return None

    def list_workers(self) -> list[dict]:
        return [dict(r) for r in self._conn.execute("SELECT * FROM workers ORDER BY created_at").fetchall()]

    def incr_task_count(self, wid: str):
        self._conn.execute("UPDATE workers SET task_count = task_count + 1 WHERE id=?", (wid,))
        self._conn.commit()

    # ── State (project facts) ──────────────────────────────

    def set_state(self, key: str, value: str, updated_by: str = ""):
        self._conn.execute(
            "INSERT INTO state (key, value, updated_by, updated_at) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_by=excluded.updated_by, updated_at=excluded.updated_at",
            (key, value, updated_by, _ts()),
        )
        self._conn.commit()

    def get_state(self, key: str) -> Optional[str]:
        row = self._conn.execute("SELECT value FROM state WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def get_all_state(self) -> dict[str, str]:
        return {r["key"]: r["value"] for r in self._conn.execute("SELECT key, value FROM state ORDER BY key").fetchall()}

    def delete_state(self, key: str):
        self._conn.execute("DELETE FROM state WHERE key=?", (key,))
        self._conn.commit()

    # ── Decisions ──────────────────────────────────────────

    def add_decision(self, worker_id: str, summary: str, reason: str = "", category: str = "general") -> int:
        cur = self._conn.execute(
            "INSERT INTO decisions (worker_id, summary, reason, category, created_at) VALUES (?, ?, ?, ?, ?)",
            (worker_id, summary, reason, category, _ts()),
        )
        self._conn.commit()
        # Also log as event
        self._log_event("decision", worker_id, payload={"summary": summary, "reason": reason, "category": category})
        return cur.lastrowid or 0

    def get_decisions(self, worker_id: Optional[str] = None, limit: int = 15) -> list[dict]:
        if worker_id:
            rows = self._conn.execute(
                "SELECT * FROM decisions WHERE worker_id=? ORDER BY created_at DESC LIMIT ?", (worker_id, limit)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def search_decisions(self, query: str, limit: int = 10) -> list[dict]:
        # Escape LIKE special chars to prevent unintended pattern matching
        escaped = query.replace("%", r"\%").replace("_", r"\_")
        rows = self._conn.execute(
            "SELECT * FROM decisions WHERE summary LIKE ? OR reason LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{escaped}%", f"%{escaped}%", limit),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Events (event sourcing) ────────────────────────────

    def _log_event(self, event_type: str, worker_id: str = "", task_id: str = "", payload: Optional[dict] = None):
        self._conn.execute(
            "INSERT INTO events (event_type, worker_id, task_id, payload, created_at) VALUES (?, ?, ?, ?, ?)",
            (event_type, worker_id, task_id, json.dumps(payload or {}), _ts()),
        )
        self._conn.commit()

    def get_events(self, limit: int = 50, event_type: Optional[str] = None) -> list[dict]:
        if event_type:
            rows = self._conn.execute(
                "SELECT * FROM events WHERE event_type=? ORDER BY created_at DESC LIMIT ?", (event_type, limit)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ── Tasks (replaces inbox messages) ────────────────────

    def create_task(self, from_worker: str, to_worker: str, payload: dict,
                    task_type: str = "request", parent_task_id: Optional[str] = None) -> str:
        tid = _uuid()
        self._conn.execute(
            "INSERT INTO tasks (id, from_worker, to_worker, task_type, payload, status, parent_task_id, created_at) VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
            (tid, from_worker, to_worker, task_type, json.dumps(payload), parent_task_id, _ts()),
        )
        self._conn.commit()
        self._log_event("task_created", from_worker, tid, {"to": to_worker, "type": task_type})
        return tid

    def get_inbox(self, worker_id: str, status: str = "pending") -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM tasks WHERE to_worker=? AND status=? ORDER BY created_at ASC LIMIT 20",
            (worker_id, status),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d.get("payload", "{}"))
            result.append(d)
        return result

    def resolve_task(self, task_id: str, status: str = "done"):
        self._conn.execute("UPDATE tasks SET status=?, resolved_at=? WHERE id=?", (status, _ts(), task_id))
        self._conn.commit()
        self._log_event("task_resolved", task_id=task_id, payload={"status": status})

    def get_task(self, task_id: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row:
            d = dict(row)
            d["payload"] = json.loads(d.get("payload", "{}"))
            return d
        return None

    def inbox_count(self, worker_id: Optional[str] = None) -> int:
        if worker_id:
            row = self._conn.execute(
                "SELECT COUNT(*) as c FROM tasks WHERE to_worker=? AND status='pending'", (worker_id,)
            ).fetchone()
        else:
            row = self._conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status='pending'").fetchone()
        return row["c"] if row else 0

    # ── Context Assembly ───────────────────────────────────

    def build_worker_context(self, worker_id: str, budget_chars: int = 4800) -> dict:
        """Build a structured context for a worker invocation within budget.

        budget_chars ≈ 1200 tokens (4 chars/token)

        Returns structured sections with estimated sizes.
        """
        worker = self.get_worker(worker_id)
        if not worker:
            return {"error": f"Worker '{worker_id}' not found"}

        state = self.get_all_state()
        decisions = self.get_decisions(worker_id, limit=10)
        inbox = self.get_inbox(worker_id)

        # Build sections within budget
        sections = {}
        remaining = budget_chars

        # 1. Identity (~100 chars / ~25 tokens)
        identity = f"Role: {worker['role']}\nConstraints: {json.dumps(worker['constraints'])}"
        sections["identity"] = identity
        remaining -= len(identity)

        # 2. Project state (~400 chars / ~100 tokens)
        if state and remaining > 200:
            state_str = "\n".join(f"{k}: {str(v)[:60]}" for k, v in list(state.items())[:15])
            state_block = f"[Project State]\n{state_str}"
            if len(state_block) > remaining:
                state_block = state_block[:remaining]
            sections["state"] = state_block
            remaining -= len(state_block)

        # 3. Decisions (~800 chars / ~200 tokens)
        if decisions and remaining > 200:
            dec_lines = []
            for d in decisions[:10]:
                line = f"- {d['summary']}"
                if d.get("reason"):
                    line += f" ({d['reason'][:60]})"
                dec_lines.append(line)
            dec_str = "\n".join(dec_lines)
            dec_block = f"[Recent Decisions]\n{dec_str}"
            if len(dec_block) > remaining:
                dec_block = dec_block[:remaining]
            sections["decisions"] = dec_block
            remaining -= len(dec_block)

        # 4. Current task (~600 chars / ~150 tokens)
        if inbox and remaining > 100:
            task = inbox[0]
            task_str = json.dumps(task["payload"], indent=2)
            task_block = f"[Current Task]\nType: {task['task_type']}\nFrom: {task['from_worker']}\nPayload:\n{task_str}"
            if len(task_block) > remaining:
                task_block = task_block[:remaining]
            sections["task"] = task_block

        return {
            "worker": worker,
            "sections": sections,
            "total_chars": budget_chars - remaining,
            "budget_chars": budget_chars,
        }

    def format_context(self, worker_id: str, budget_chars: int = 4800) -> str:
        """Build and format a complete worker context string."""
        ctx = self.build_worker_context(worker_id, budget_chars)
        if "error" in ctx:
            return ctx["error"]

        parts = [f"[IDENTITY]\n{ctx['sections'].get('identity', '')}"]
        if "state" in ctx.get("sections", {}):
            parts.append(ctx["sections"]["state"])
        if "decisions" in ctx.get("sections", {}):
            parts.append(ctx["sections"]["decisions"])
        if "task" in ctx.get("sections", {}):
            parts.append(ctx["sections"]["task"])

        return "\n\n".join(parts)

    # ── Utility ────────────────────────────────────────────

    def get_stats(self) -> dict:
        return {
            "workers": self._conn.execute("SELECT COUNT(*) as c FROM workers").fetchone()["c"],
            "state_keys": self._conn.execute("SELECT COUNT(*) as c FROM state").fetchone()["c"],
            "decisions": self._conn.execute("SELECT COUNT(*) as c FROM decisions").fetchone()["c"],
            "events": self._conn.execute("SELECT COUNT(*) as c FROM events").fetchone()["c"],
            "pending_tasks": self._conn.execute("SELECT COUNT(*) as c FROM tasks WHERE status='pending'").fetchone()["c"],
        }
