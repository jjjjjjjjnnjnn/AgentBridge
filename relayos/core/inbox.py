"""Worker Inbox — message passing between agent workers.

Each worker has an inbox that other workers can send messages to.
Messages persist in SQLite across sessions.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class WorkerInbox:
    """Inbox system for agent workers.

    Each worker (identified by terminal_id) can:
    - receive messages from other workers
    - send messages to other workers
    - list unread messages
    - mark messages as read
    """

    def __init__(self, db_path: str = "~/.relayos/inbox.db"):
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
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_worker TEXT NOT NULL,
                    to_worker TEXT NOT NULL,
                    subject TEXT DEFAULT '',
                    body TEXT NOT NULL,
                    status TEXT DEFAULT 'unread',
                    created_at TEXT NOT NULL,
                    read_at TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_inbox
                ON messages(to_worker, status)
            """)
            conn.commit()

    def send(self, to: str, body: str, subject: str = "", from_worker: str = "system") -> int:
        """Send a message to a worker. Returns message ID."""
        ts = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO messages (from_worker, to_worker, subject, body, status, created_at) VALUES (?, ?, ?, ?, 'unread', ?)",
            (from_worker, to, subject, body, ts),
        )
        self._conn.commit()
        return self._conn.lastrowid or 0

    def list_inbox(self, worker: str, unread_only: bool = True) -> list[dict[str, Any]]:
        """List messages for a worker."""
        if unread_only:
            rows = self._conn.execute(
                "SELECT * FROM messages WHERE to_worker = ? AND status = 'unread' ORDER BY created_at DESC",
                (worker,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM messages WHERE to_worker = ? ORDER BY created_at DESC LIMIT 50",
                (worker,),
            ).fetchall()
        return [dict(r) for r in rows]

    def mark_read(self, message_id: int) -> bool:
        """Mark a message as read."""
        ts = datetime.now(timezone.utc).isoformat()
        cur = self._conn.execute(
            "UPDATE messages SET status = 'read', read_at = ? WHERE id = ?",
            (ts, message_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def count_unread(self, worker: str) -> int:
        """Count unread messages for a worker."""
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM messages WHERE to_worker = ? AND status = 'unread'",
            (worker,),
        ).fetchone()
        return row["cnt"] if row else 0

    def delete_message(self, message_id: int) -> bool:
        """Delete a message."""
        cur = self._conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def get_stats(self) -> dict:
        """Get inbox statistics."""
        total = self._conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()
        unread = self._conn.execute("SELECT COUNT(*) as c FROM messages WHERE status = 'unread'").fetchone()
        per_worker = self._conn.execute(
            "SELECT to_worker, COUNT(*) as c FROM messages WHERE status = 'unread' GROUP BY to_worker"
        ).fetchall()
        return {
            "total": total["c"] if total else 0,
            "unread": unread["c"] if unread else 0,
            "per_worker": {r["to_worker"]: r["c"] for r in per_worker} if per_worker else {},
        }
