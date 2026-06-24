"""Artifact Store — persistent storage for structured step outputs.

Each step in a capability graph produces a structured artifact.
Subsequent steps reference artifacts by ID and extract only
the fields they need (defined by their schema).
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


def _aid() -> str:
    return f"art-{uuid.uuid4().hex[:12]}"


class ArtifactStore:
    """Stores structured step outputs and enables field-level extraction."""

    def __init__(self, db_path: str = "~/.relayos/artifacts.db"):
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
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    step_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model_used TEXT DEFAULT '',
                    tokens_used INTEGER DEFAULT 0,
                    created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_art_session ON artifacts(session_id);
            """)
            conn.commit()

    def store(self, session_id: str, step_id: str, step_type: str,
              content: dict, model_used: str = "", tokens_used: int = 0) -> str:
        """Store a structured step output. Returns artifact ID."""
        aid = _aid()
        now = _ts()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (aid, session_id, step_id, step_type, json.dumps(content),
                 model_used, tokens_used, now),
            )
            conn.commit()
        return aid

    def get(self, artifact_id: str) -> Optional[dict]:
        """Retrieve an artifact by ID."""
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE id=?", (artifact_id,)
        ).fetchone()
        if row:
            d = dict(row)
            d["content"] = json.loads(d["content"])
            return d
        return None

    def get_by_step(self, session_id: str, step_id: str) -> Optional[dict]:
        """Get the artifact for a specific step in a session."""
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE session_id=? AND step_id=? ORDER BY created_at DESC LIMIT 1",
            (session_id, step_id),
        ).fetchone()
        if row:
            d = dict(row)
            d["content"] = json.loads(d["content"])
            return d
        return None

    def get_by_type(self, session_id: str, step_type: str) -> Optional[dict]:
        """Get the latest artifact of a given type in a session."""
        row = self._conn.execute(
            "SELECT * FROM artifacts WHERE session_id=? AND step_type=? ORDER BY created_at DESC LIMIT 1",
            (session_id, step_type),
        ).fetchone()
        if row:
            d = dict(row)
            d["content"] = json.loads(d["content"])
            return d
        return None

    def extract_fields(self, session_id: str, step_type: str,
                       fields: list[str]) -> dict[str, Any]:
        """Extract specific fields from an upstream step type's artifact.

        This is the key method for token-efficient graph execution.
        Instead of passing full text, it only returns the fields
        that the downstream step's schema declares as 'consumes'.
        """
        artifact = self.get_by_type(session_id, step_type)
        if not artifact:
            return {}

        content = artifact["content"]
        result = {}
        for field in fields:
            if field in content:
                value = content[field]
                if isinstance(value, list):
                    # Limit lists to first 5 items
                    result[field] = value[:5]
                elif isinstance(value, str):
                    result[field] = value[:200]
                else:
                    result[field] = value
        return result

    def get_session_artifacts(self, session_id: str) -> list[dict]:
        """Get all artifacts for a session, ordered by creation time."""
        rows = self._conn.execute(
            "SELECT * FROM artifacts WHERE session_id=? ORDER BY created_at ASC",
            (session_id,),
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["content"] = json.loads(d["content"])
            result.append(d)
        return result

    def delete_session(self, session_id: str):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM artifacts WHERE session_id=?", (session_id,))
            conn.commit()
