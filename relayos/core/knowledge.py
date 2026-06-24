"""Knowledge System — cross-session project memory.

Two new tables:
1. project_knowledge: cross-session, project-level facts
2. session_summaries: session completion summaries

KnowledgeCompiler runs after each session, extracts structured facts
from artifacts, and stores them in project_knowledge.

Zero LLM, pure code, rule-driven extraction.
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


def _uid() -> str:
    return f"proj-{uuid.uuid4().hex[:8]}"


class ProjectStore:
    """Cross-session project knowledge and session summaries."""

    def __init__(self, db_path: str = "~/.relayos/knowledge.db"):
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
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    created_at INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS project_knowledge (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    domain TEXT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    source_session TEXT,
                    source_step TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    UNIQUE(project_id, key)
                );
                CREATE TABLE IF NOT EXISTS session_summaries (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    goal TEXT,
                    outcome TEXT DEFAULT 'completed',
                    key_decisions TEXT DEFAULT '[]',
                    knowledge_added TEXT DEFAULT '[]',
                    total_tokens INTEGER DEFAULT 0,
                    created_at INTEGER NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_knowledge_project ON project_knowledge(project_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_domain ON project_knowledge(project_id, domain);
                CREATE INDEX IF NOT EXISTS idx_summary_project ON session_summaries(project_id);
            """)
            conn.commit()

    # ── Projects ──────────────────────────────────────────────

    def create_project(self, name: str, description: str = "") -> str:
        pid = _uid()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("INSERT INTO projects (id, name, description, created_at) VALUES (?, ?, ?, ?)",
                         (pid, name, description, _ts()))
            conn.commit()
        return pid

    def get_project(self, pid: str) -> Optional[dict]:
        row = self._conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
        return dict(row) if row else None

    def list_projects(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT p.*, (SELECT COUNT(*) FROM project_knowledge WHERE project_id=p.id) as knowledge_count, "
            "(SELECT COUNT(*) FROM session_summaries WHERE project_id=p.id) as session_count "
            "FROM projects p ORDER BY p.created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Knowledge ─────────────────────────────────────────────

    def upsert_knowledge(self, project_id: str, domain: str, key: str, value: str,
                         source_session: str = "", source_step: str = "") -> str:
        kid = f"know-{uuid.uuid4().hex[:12]}"
        now = _ts()
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                INSERT INTO project_knowledge (id, project_id, domain, key, value, confidence, source_session, source_step, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 1.0, ?, ?, ?, ?)
                ON CONFLICT(project_id, key) DO UPDATE SET
                    value=excluded.value, confidence=1.0,
                    source_session=excluded.source_session,
                    updated_at=excluded.updated_at
            """, (kid, project_id, domain, key, value, source_session, source_step, now, now))
            conn.commit()
        return kid

    def query_knowledge(self, project_id: str, domain: Optional[str] = None,
                        max_items: int = 8) -> list[dict]:
        if domain:
            rows = self._conn.execute("""
                SELECT * FROM project_knowledge
                WHERE project_id=? AND domain=? AND confidence>0.5
                ORDER BY confidence DESC, updated_at DESC LIMIT ?
            """, (project_id, domain, max_items)).fetchall()
        else:
            rows = self._conn.execute("""
                SELECT * FROM project_knowledge
                WHERE project_id=? AND confidence>0.5
                ORDER BY confidence DESC, updated_at DESC LIMIT ?
            """, (project_id, max_items)).fetchall()
        return [dict(r) for r in rows]

    def update_confidence(self, project_id: str, key: str, confidence: float):
        self._conn.execute(
            "UPDATE project_knowledge SET confidence=?, updated_at=? WHERE project_id=? AND key=?",
            (confidence, _ts(), project_id, key),
        )
        self._conn.commit()

    # ── Session Summaries ─────────────────────────────────────

    def save_summary(self, project_id: str, session_id: str, goal: str = "",
                     outcome: str = "completed",
                     key_decisions: Optional[list] = None,
                     knowledge_added: Optional[list] = None,
                     total_tokens: int = 0) -> str:
        sid = f"sum-{uuid.uuid4().hex[:12]}"
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO session_summaries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (sid, project_id, session_id, goal, outcome,
                 json.dumps(key_decisions or []),
                 json.dumps(knowledge_added or []),
                 total_tokens, _ts()),
            )
            conn.commit()
        return sid

    def get_project_summary(self, project_id: str) -> dict:
        """Get a summary of all knowledge for a project."""
        knowledge = self.query_knowledge(project_id, max_items=50)
        sessions = self._conn.execute(
            "SELECT * FROM session_summaries WHERE project_id=? ORDER BY created_at DESC LIMIT 10",
            (project_id,),
        ).fetchall()

        # Group knowledge by domain
        by_domain: dict[str, list[dict]] = {}
        for k in knowledge:
            domain = k.get("domain", "general")
            by_domain.setdefault(domain, []).append(k)

        return {
            "total_knowledge": len(knowledge),
            "by_domain": {d: len(items) for d, items in by_domain.items()},
            "recent_sessions": [dict(s) for s in sessions],
        }


EXTRACTION_RULES: dict[str, dict[str, str]] = {
    "research": {
        "findings": "knowledge.{domain}.findings",
        "constraints": "knowledge.{domain}.constraints",
    },
    "architecture": {
        "decisions": "decision.{component}",
    },
    "review": {
        "verdict": "knowledge.{domain}.review_verdict",
    },
    "coding": {
        "impl_decisions": "decision.impl.{component}",
    },
}


class KnowledgeCompiler:
    """Extracts structured knowledge from session artifacts.

    Runs after each session. Pure code, zero LLM calls.
    Maps artifact fields to project_knowledge keys via rules.
    """

    def __init__(self):
        self.store = ProjectStore()

    def compile(self, session_id: str, project_id: str,
                goal: str = "", artifacts: Optional[list] = None) -> dict:
        """Compile session artifacts into project knowledge.

        Args:
            session_id: Session to compile
            project_id: Project to store knowledge under
            goal: Session goal (for domain inference)
            artifacts: List of artifact dicts. If None, fetched from store.

        Returns:
            Summary of what was added
        """
        from relayos.core.artifacts import ArtifactStore
        art_store = ArtifactStore()

        if artifacts is None:
            art_list = art_store.get_session_artifacts(session_id)
        else:
            art_list = artifacts

        domain = self._infer_domain(goal)
        new_keys = []
        decisions = []

        for art in art_list:
            step_type = art.get("step_type", "")
            content = art.get("content", {})
            rules = EXTRACTION_RULES.get(step_type, {})

            for field, key_template in rules.items():
                value = content.get(field)
                if not value:
                    continue

                key = key_template.format(
                    domain=domain,
                    component=step_type,
                )

                self.store.upsert_knowledge(
                    project_id=project_id,
                    domain=domain,
                    key=key,
                    value=json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value,
                    source_session=session_id,
                    source_step=step_type,
                )
                new_keys.append(key)

                # Track decisions for summary
                if key.startswith("decision."):
                    decisions.append({"key": key, "value": value})

        # Save session summary
        self.store.save_summary(
            project_id=project_id,
            session_id=session_id,
            goal=goal,
            key_decisions=decisions,
            knowledge_added=new_keys,
        )

        return {
            "knowledge_added": len(new_keys),
            "decisions": len(decisions),
            "keys": new_keys[:10],
        }

    def build_skip_instructions(self, project_id: str, domain: str,
                                step_type: str) -> str:
        """Generate skip instructions from prior knowledge.

        Tells the step what's already known so it doesn't rediscover.
        """
        knowledge = self.store.query_knowledge(project_id, domain, max_items=8)
        if not knowledge:
            return ""

        if step_type == "research":
            known = [k for k in knowledge if "constraint" in k.get("key", "")
                     or "finding" in k.get("key", "")]
            if known:
                parts = ["Known information (no need to rediscover):"]
                for k in known[:5]:
                    val = k.get("value", "")[:120]
                    parts.append(f"  - {k['key']}: {val}")
                return "\n".join(parts)

        if step_type == "architecture":
            decisions = [k for k in knowledge if "decision" in k.get("key", "")]
            if decisions:
                parts = ["Existing decisions (apply directly):"]
                for d in decisions[:5]:
                    val = d.get("value", "")[:120]
                    parts.append(f"  - {d['key']}: {val}")
                return "\n".join(parts)

        return ""

    def _infer_domain(self, goal: str) -> str:
        """Infer domain from session goal."""
        goal_lower = goal.lower()
        for keyword, domain in [
            ("payment", "payment"), ("auth", "auth"), ("user", "auth"),
            ("api", "api"), ("database", "data"), ("db", "data"),
            ("frontend", "ui"), ("ui", "ui"), ("test", "qa"),
            ("deploy", "infra"), ("infra", "infra"),
        ]:
            if keyword in goal_lower:
                return domain
        return "general"
