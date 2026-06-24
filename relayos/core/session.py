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
                CREATE TABLE IF NOT EXISTS conversation_graph (
                    child_id TEXT NOT NULL,
                    parent_id TEXT NOT NULL,
                    PRIMARY KEY (child_id, parent_id),
                    FOREIGN KEY (child_id) REFERENCES sessions(id),
                    FOREIGN KEY (parent_id) REFERENCES sessions(id)
                );
                CREATE INDEX IF NOT EXISTS idx_msg_session ON messages(session_id, created_at);
                CREATE INDEX IF NOT EXISTS idx_graph_parent ON conversation_graph(parent_id);
                CREATE INDEX IF NOT EXISTS idx_graph_child ON conversation_graph(child_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_project ON sessions(project_id);
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
            conn.execute("DELETE FROM conversation_graph WHERE child_id=? OR parent_id=?", (sid, sid))
            conn.execute("DELETE FROM sessions WHERE id=?", (sid,))
            conn.commit()

    # ── Conversation Graph ──────────────────────────────────

    def add_integrated_conversation(self, child_id: str, parent_ids: list[str]):
        """Record that a conversation was created by merging parent conversations."""
        with sqlite3.connect(self._db_path) as conn:
            for pid in parent_ids:
                conn.execute("INSERT OR IGNORE INTO conversation_graph (child_id, parent_id) VALUES (?, ?)",
                             (child_id, pid))
            conn.commit()

    def fork_session(self, parent_id: str, name: str = "") -> Session:
        """Create a new session that's a fork of an existing one.

        The child session copies the parent's messages.
        """
        parent = self.get_session(parent_id)
        if not parent:
            raise ValueError(f"Session '{parent_id}' not found")
        child = self.create_session(name or f"Fork of {parent.name}", parent.mode,
                                     parent.participants, parent.profile, parent.project_id)
        # Copy messages from parent
        msgs = self.get_messages(parent_id, limit=200)
        for m in msgs:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    "INSERT INTO messages (id, session_id, role, from_worker, content, event_type, model, tokens, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (f"msg-{uuid.uuid4().hex[:8]}", child.id, m.role, m.from_worker, m.content, m.event_type, m.model, m.tokens, m.created_at),
                )
                conn.commit()
        # Record graph edge: child was forked FROM parent
        self.add_integrated_conversation(child.id, [parent_id])
        return child

    def merge_sessions(self, session_ids: list[str], name: str = "",
                       profile: str = "balanced") -> Session:
        """Merge multiple sessions into one integrated conversation.

        The new session combines messages from all parents.
        """
        child = self.create_session(name or f"Merge of {len(session_ids)} sessions",
                                     "integrated", profile=profile)
        # Record all parents
        self.add_integrated_conversation(child.id, session_ids)
        # Copy all messages from parents
        for pid in session_ids:
            msgs = self.get_messages(pid, limit=100)
            for m in msgs:
                with sqlite3.connect(self._db_path) as conn:
                    conn.execute(
                        "INSERT INTO messages (id, session_id, role, from_worker, content, event_type, model, tokens, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (f"msg-{uuid.uuid4().hex[:8]}", child.id, m.role, m.from_worker, m.content, m.event_type, m.model, m.tokens, m.created_at),
                    )
                    conn.commit()
        return child

    def get_parent_summary(self, sid: str) -> str:
        """Get a human-readable summary of parent sessions."""
        parents = self.get_conversation_parents(sid)
        if not parents:
            return ""
        names = []
        for pid in parents:
            p = self.get_session(pid)
            names.append(p.name[:15] if p else pid[:8])
        return "Derived: " + ", ".join(f"#{pid[:6]}" for pid in parents)

    def get_conversation_parents(self, sid: str) -> list[str]:
        """Get the IDs of conversations that were merged into this one."""
        rows = self._conn.execute(
            "SELECT parent_id FROM conversation_graph WHERE child_id=? ORDER BY parent_id",
            (sid,)
        ).fetchall()
        return [r["parent_id"] for r in rows]

    def get_conversation_children(self, sid: str) -> list[str]:
        """Get the IDs of conversations that were created FROM this one."""
        rows = self._conn.execute(
            "SELECT child_id FROM conversation_graph WHERE parent_id=? ORDER BY child_id",
            (sid,)
        ).fetchall()
        return [r["child_id"] for r in rows]

    def get_conversation_graph(self, sid: str) -> dict:
        """Get the full graph context for a conversation (ancestors + descendants)."""
        parents = self.get_conversation_parents(sid)
        children = self.get_conversation_children(sid)
        grandparents = []
        for p in parents:
            grandparents.extend(self.get_conversation_parents(p))
        return {
            "ancestors": parents + grandparents,
            "descendants": children,
            "all": list(set(parents + grandparents + children)),
        }

    def get_all_graph_edges(self) -> list[tuple[str, str]]:
        """Get ALL graph edges for full graph rendering."""
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT parent_id, child_id FROM conversation_graph ORDER BY parent_id"
            ).fetchall()
            return [(r["parent_id"], r["child_id"]) for r in rows]

    def build_graph_ascii(self, highlight_id: str = "") -> str:
        """Build an ASCII tree of the conversation graph.

        Shows all sessions with fork/merge relationships.
        Use box-drawing characters for visual tree.
        """
        edges = self.get_all_graph_edges()
        if not edges:
            return "  (no graph yet. use /fork, /merge to create one.)"

        children_of = {}
        all_ids = set()
        for p, c in edges:
            children_of.setdefault(p, []).append(c)
            all_ids.add(p)
            all_ids.add(c)

        has_parent = {c for _, c in edges}
        roots = sorted(all_ids - has_parent, key=lambda x: x or "")

        names = {}
        for sid in all_ids:
            s = self.get_session(sid)
            names[sid] = s.name[:20] if s else sid[:8]

        lines = []

        def render(sid, prefix="", last=True):
            kids = children_of.get(sid, [])
            marker = "└── " if last else "├── "
            conn_pre = "    " if last else "│   "
            hl = " >" if sid == highlight_id else "  "
            label = f"{names.get(sid, sid[:8])} [{sid[:6]}]"
            lines.append(f"{prefix}{marker}{hl}{label}")
            for i, k in enumerate(kids):
                render(k, prefix + conn_pre, i == len(kids) - 1)

        if len(roots) == 1:
            render(roots[0], "", True)
        else:
            for i, r in enumerate(roots):
                last = (i == len(roots) - 1)
                marker = "└── " if last else "├── "
                hl = " >" if r == highlight_id else "  "
                label = f"{names.get(r, r[:8])} [{r[:6]}]"
                lines.append(f"{marker}{hl}{label}")
                kids = children_of.get(r, [])
                conn_pre = "    " if last else "│   "
                for j, k in enumerate(kids):
                    render(k, conn_pre, j == len(kids) - 1)

        return "\n".join(lines) if lines else "  (empty)"

    def list_project_conversations(self, project_id: str, limit: int = 20) -> list[dict]:
        """List all conversations in a project."""
        if not project_id:
            return self.list_sessions(limit)
        rows = self._conn.execute(
            "SELECT id, name, mode, profile, project_id, last_worker, last_model, last_capability, last_strategy, created_at, updated_at, "
            "(SELECT COUNT(*) FROM messages WHERE session_id=sessions.id) as msg_count "
            "FROM sessions WHERE project_id=? ORDER BY updated_at DESC LIMIT ?",
            (project_id, limit)
        ).fetchall()
        return [dict(r) for r in rows]
