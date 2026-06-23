"""Shared memory — dict + SQLite persistent store."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class MemoryStore:
    """Simple key-value memory with SQLite persistence.

    Each agent can read/write to the same store,
    enabling cross-agent context sharing.
    """

    def __init__(self, db_path: str = "~/.agentmesh/memory.db"):
        self._local = threading.local()
        path = Path(db_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db_path = str(path)
        self._init_db()

    @property
    def _conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS session_memory (
                session_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                step INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                PRIMARY KEY (session_id, key)
            )
        """)
        conn.commit()
        conn.close()

    def set(self, key: str, value: Any, session_id: Optional[str] = None):
        """Store a value (serialized as JSON if not string)."""
        now = datetime.now(timezone.utc).isoformat()
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)

        if session_id:
            self._conn.execute(
                "INSERT OR REPLACE INTO session_memory (session_id, key, value, step, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, key, value, 0, now),
            )
        else:
            self._conn.execute(
                "INSERT OR REPLACE INTO memory (key, value, created_at, updated_at) VALUES (?, ?, COALESCE((SELECT created_at FROM memory WHERE key=?), ?), ?)",
                (key, value, key, now, now),
            )
        self._conn.commit()

    def get(self, key: str, session_id: Optional[str] = None, default: Any = None) -> Any:
        """Retrieve a value."""
        if session_id:
            row = self._conn.execute(
                "SELECT value FROM session_memory WHERE session_id = ? AND key = ?",
                (session_id, key),
            ).fetchone()
        else:
            row = self._conn.execute(
                "SELECT value FROM memory WHERE key = ?", (key,)
            ).fetchone()

        if row is None:
            return default
        return row["value"]

    def get_all(self, session_id: Optional[str] = None) -> dict[str, Any]:
        """Retrieve all keys."""
        if session_id:
            rows = self._conn.execute(
                "SELECT key, value FROM session_memory WHERE session_id = ? ORDER BY step",
                (session_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT key, value FROM memory ORDER BY key"
            ).fetchall()
        return {r["key"]: r["value"] for r in rows}

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """Simple substring search across memory keys and values."""
        rows = self._conn.execute(
            "SELECT key, value, updated_at FROM memory WHERE key LIKE ? OR value LIKE ? LIMIT ?",
            (f"%{query}%", f"%{query}%", limit),
        ).fetchall()
        return [{"key": r["key"], "value": r["value"], "updated_at": r["updated_at"]} for r in rows]

    def clear(self, session_id: Optional[str] = None):
        if session_id:
            self._conn.execute("DELETE FROM session_memory WHERE session_id = ?", (session_id,))
        else:
            self._conn.execute("DELETE FROM memory")
            self._conn.execute("DELETE FROM sessions")
            self._conn.execute("DELETE FROM session_memory")
        self._conn.commit()
