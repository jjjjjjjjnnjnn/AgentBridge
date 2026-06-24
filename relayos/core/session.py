"""Session — the core abstraction for all AI interactions.

A Session is an "AI collaboration room":
- Has participants (workers/models)
- Tracks messages as structured events
- Has a router (scheduler) for model selection
- Has memory state
- Has constraints (budget, concurrency)

All interaction modes (chat, ask, group) use sessions internally.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def _uid() -> str:
    return f"sess-{uuid.uuid4().hex[:8]}"


@dataclass
class SessionMessage:
    id: str
    session_id: str
    role: str  # "user" | "assistant" | "system"
    from_worker: str  # worker name or "user"
    content: str
    event_type: str = "message"  # message | task | decision | finding | result
    model: str = ""
    tokens: int = 0
    created_at: int = field(default_factory=_ts)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "from": self.from_worker,
            "content": self.content[:200],
            "event_type": self.event_type,
            "model": self.model,
            "tokens": self.tokens,
        }


@dataclass
class Session:
    id: str
    name: str
    mode: str = "chat"  # chat | ask | group
    project_id: str = ""  # project this session belongs to
    participants: list[str] = field(default_factory=list)
    profile: str = "balanced"
    last_worker: str = ""  # last model used (informational)
    last_model: str = ""
    last_capability: str = ""  # last task type detected: coding|architecture|review|research|writing
    last_strategy: str = ""  # last scheduling strategy: free-first|quality|balanced
    max_parallel: int = 3
    max_models: int = 4
    created_at: int = field(default_factory=_ts)
    updated_at: int = field(default_factory=_ts)


class SessionStore:
    """Persistent storage for sessions and their messages."""

    def __init__(self, db_path: str = "~/.relayos/sessions.db"):
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
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    mode TEXT DEFAULT 'chat',
                    participants TEXT DEFAULT '[]',
                    project_id TEXT DEFAULT '',
                    profile TEXT DEFAULT 'balanced',
                    last_worker TEXT DEFAULT '',
                    last_model TEXT DEFAULT '',
                    last_capability TEXT DEFAULT '',
                    last_strategy TEXT DEFAULT '',
                    max_parallel INTEGER DEFAULT 3,
                    max_models INTEGER DEFAULT 4,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    from_worker TEXT NOT NULL,
                    content TEXT NOT NULL,
                    event_type TEXT DEFAULT 'message',
                    model TEXT DEFAULT '',
                    tokens INTEGER DEFAULT 0,
                    created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id, created_at);
            """)
            conn.commit()

        # Migration for existing databases: add columns atomically
        try:
            with sqlite3.connect(self._db_path) as conn:
                existing = [r[1] for r in conn.execute("PRAGMA table_info(sessions)").fetchall()]
                migrations = [
                    "ALTER TABLE sessions ADD COLUMN last_worker TEXT DEFAULT ''",
                    "ALTER TABLE sessions ADD COLUMN last_model TEXT DEFAULT ''",
                    "ALTER TABLE sessions ADD COLUMN last_capability TEXT DEFAULT ''",
                    "ALTER TABLE sessions ADD COLUMN last_strategy TEXT DEFAULT ''",
                    "ALTER TABLE sessions ADD COLUMN project_id TEXT DEFAULT ''",
                ]
                for stmt in migrations:
                    col = stmt.split()[3]
                    if col not in existing:
                        conn.execute(stmt)
                conn.commit()
        except sqlite3.OperationalError:
            pass  # migration not needed on fresh db

    # ── Sessions ──────────────────────────────────────────

    def create_session(self, name: str, mode: str = "chat",
                       participants: Optional[list[str]] = None,
                       profile: str = "balanced",
                       project_id: str = "",
                       last_capability: str = "", last_strategy: str = "") -> Session:
        sid = _uid()
        now = _ts()
        parts = json.dumps(participants or [])
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO sessions (id, name, mode, participants, project_id, profile, last_worker, last_model, last_capability, last_strategy, max_parallel, max_models, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (sid, name, mode, parts, project_id, profile, '', '', last_capability, last_strategy, 3, 4, now, now),
            )
            conn.commit()
        return Session(id=sid, name=name, mode=mode, participants=participants or [],
                       project_id=project_id, profile=profile,
                       last_capability=last_capability, last_strategy=last_strategy,
                       created_at=now, updated_at=now)

    def get_session(self, sid: str) -> Optional[Session]:
        row = self._conn.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
        if row:
            row_dict = dict(row)
            return Session(
                id=row_dict["id"], name=row_dict["name"], mode=row_dict["mode"],
                participants=json.loads(row_dict.get("participants", "[]")),
                profile=row_dict.get("profile", "balanced"),
                last_worker=row_dict.get("last_worker", ""),
                last_model=row_dict.get("last_model", ""),
                last_capability=row_dict.get("last_capability", ""),
                last_strategy=row_dict.get("last_strategy", ""),
                project_id=row_dict.get("project_id", ""),
                max_parallel=row_dict.get("max_parallel", 3),
                max_models=row_dict.get("max_models", 4),
                created_at=row_dict["created_at"], updated_at=row_dict["updated_at"],
            )
        return None

    def list_sessions(self, limit: int = 10) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, name, mode, profile, project_id, last_worker, last_model, last_capability, last_strategy, created_at, updated_at, "
            "(SELECT COUNT(*) FROM messages WHERE session_id=sessions.id) as msg_count "
            "FROM sessions ORDER BY updated_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_session_time(self, sid: str):
        self._conn.execute("UPDATE sessions SET updated_at=? WHERE id=?", (_ts(), sid))
        self._conn.commit()

    def set_last_used(self, sid: str, worker: str = "", model: str = "",
                      capability: str = "", strategy: str = ""):
        self._conn.execute(
            "UPDATE sessions SET last_worker=?, last_model=?, last_capability=?, last_strategy=?, updated_at=? WHERE id=?",
            (worker, model, capability, strategy, _ts(), sid),
        )
        self._conn.commit()

    # ── Messages ──────────────────────────────────────────

    def add_message(self, session_id: str, role: str, from_worker: str, content: str,
                    event_type: str = "message", model: str = "", tokens: int = 0) -> SessionMessage:
        mid = f"msg-{uuid.uuid4().hex[:8]}"
        now = _ts()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (mid, session_id, role, from_worker, content, event_type, model, tokens, now),
            )
            conn.commit()
        self.update_session_time(session_id)
        return SessionMessage(id=mid, session_id=session_id, role=role,
                              from_worker=from_worker, content=content,
                              event_type=event_type, model=model, tokens=tokens, created_at=now)

    def get_messages(self, session_id: str, limit: int = 50) -> list[SessionMessage]:
        rows = self._conn.execute(
            "SELECT * FROM messages WHERE session_id=? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return [SessionMessage(**dict(r)) for r in rows]

    def get_timeline(self, session_id: str, limit: int = 20) -> list[dict]:
        """Get formatted timeline for UI display."""
        msgs = self.get_messages(session_id, limit)
        return [m.to_dict() for m in msgs]

    def delete_session(self, sid: str):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM messages WHERE session_id=?", (sid,))
            conn.execute("DELETE FROM sessions WHERE id=?", (sid,))
            conn.commit()
