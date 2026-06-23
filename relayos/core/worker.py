"""Worker Manager — persistent AI team members.

A Worker is a logical entity with:
- A role (architect, researcher, coder, reviewer)
- A provider/model assignment
- Persistent state (project facts it knows)
- An inbox (task-based, not message-based)
- Status tracking across sessions

Workers are the user-facing concept. They bridge between:
- Provider adapters (for API calls)
- Terminal types (for CLI execution)
- The user's mental model ("my architect knows my project")
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from relayos.adapters import get_adapter
from relayos.config import load_config
from relayos.core.compiler import StateCompiler
from relayos.core.state import StateStore

logger = logging.getLogger(__name__)
from relayos.orchestrator.pool import TerminalPool

logger = logging.getLogger(__name__)

# Default worker roles with recommended provider/model
DEFAULT_ROLES: dict[str, dict[str, str]] = {
    "architect": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "emoji": "🧠",
        "description": "System design, architecture decisions",
    },
    "researcher": {
        "provider": "google",
        "model": "gemini-2.5-flash",
        "emoji": "🔍",
        "description": "Research, analysis, data gathering",
    },
    "coder": {
        "provider": "openai",
        "model": "gpt-4o",
        "emoji": "⭐",
        "description": "Code generation, implementation",
    },
    "reviewer": {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "emoji": "🎯",
        "description": "Code review, security audit",
    },
    "debugger": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "emoji": "🐛",
        "description": "Debugging, error analysis",
    },
    "writer": {
        "provider": "openai",
        "model": "gpt-4o",
        "emoji": "✍️",
        "description": "Documentation, writing",
    },
    "assistant": {
        "provider": "anthropic",
        "model": "claude-haiku-4-20251001",
        "emoji": "💡",
        "description": "General assistant, quick tasks",
    },
    "data-engineer": {
        "provider": "deepseek",
        "model": "deepseek-chat",
        "emoji": "📊",
        "description": "Data processing, ETL, analysis",
    },
}


@dataclass
class Worker:
    name: str
    role: str
    provider: str
    model: str
    emoji: str = "🤖"
    status: str = "idle"  # idle | busy | error
    description: str = ""
    task_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_used: Optional[str] = None


class WorkerManager:
    """Manages the AI workforce — create, list, assign tasks to workers.

    Workers are the primary user-facing concept. Each worker has:
    - A name and role (user gives it identity)
    - A provider + model (what powers it)
    - Persistent state via StateStore (project facts, decisions, tasks)
    - An inbox (tasks from other workers/user)
    - Persistence across sessions (SQLite via StateStore)
    """

    def __init__(self, config_path: Optional[str] = None):
        self._workers: dict[str, Worker] = {}
        self._lock = threading.Lock()
        self.store = StateStore()
        self.compiler = StateCompiler(self.store)
        self.config = load_config(Path(config_path) if config_path else None)
        self._load_from_store()

    def _load_from_store(self):
        """Load workers from StateStore. Create defaults if empty."""
        db_workers = self.store.list_workers()
        if not db_workers:
            self._create_defaults()
            return
        for w in db_workers:
            worker = Worker(
                name=w["id"], role=w["role"],
                provider=w.get("provider", ""),
                model=w.get("model", ""),
                status="idle",
                task_count=w.get("task_count", 0),
            )
            self._workers[worker.name] = worker

    def _create_defaults(self):
        for name, role_def in DEFAULT_ROLES.items():
            self.create(name=name, role=name, **role_def)

    def create(self, name: str, role: str, provider: str, model: str,
               emoji: str = "🤖", description: str = "") -> Worker:
        """Create a new worker and persist via StateStore."""
        w = Worker(name=name, role=role, provider=provider, model=model, emoji=emoji, description=description)
        with self._lock:
            self._workers[name] = w
        self.store.upsert_worker(name, role, provider, model)
        logger.info(f"Worker '{name}' created — {provider}/{model}")
        return w

    def get(self, name: str) -> Optional[Worker]:
        return self._workers.get(name)

    def list(self) -> list[Worker]:
        return list(self._workers.values())

    def remove(self, name: str) -> bool:
        with self._lock:
            if name in self._workers:
                del self._workers[name]
        # StateStore doesn't have delete_worker yet, use raw SQL
        import sqlite3
        db = str(Path("~/.relayos/state.db").expanduser())
        with sqlite3.connect(db) as conn:
            conn.execute("DELETE FROM workers WHERE id=?", (name,))
            conn.commit()
        return True

    def run(self, worker_name: str, prompt: str, **kwargs) -> str:
        """Run a prompt on a specific worker via its provider adapter."""
        w = self.get(worker_name)
        if not w:
            raise ValueError(f"Worker '{worker_name}' not found")

        w.status = "busy"
        w.task_count += 1

        try:
            adapter = get_adapter(w.provider, {
                "api_key": self.config.resolve_api_key(w.provider),
                "model": w.model,
            })
            response = adapter.chat(prompt, **kwargs)

            # Store result as structured state (not chat history)
            self.store.set_state(f"worker:{worker_name}:last_output", response.content[:500], updated_by=worker_name)
            self.store.incr_task_count(worker_name)

            # Auto-extract decision if output looks structured
            try:
                parsed = json.loads(response.content)
                if isinstance(parsed, dict):
                    self.compiler.resolve(worker_name, parsed)
            except (json.JSONDecodeError, TypeError):
                pass  # free-form output, no structured parsing

            w.status = "idle"
            return response.content
        except Exception as e:
            w.status = "error"
            raise

    def send_task(self, from_worker: str, to_worker: str, task_body: str, task_type: str = "request") -> str:
        """Send a task from one worker to another via StateStore."""
        return self.store.create_task(
            from_worker=from_worker,
            to_worker=to_worker,
            payload={"body": task_body, "type": task_type},
            task_type=task_type,
        )

    def get_team(self) -> list[dict[str, Any]]:
        """Get the full team status (like 'htop' for AI workers)."""
        result = []
        all_state = self.store.get_all_state()
        for w in self.list():
            unread = self.store.inbox_count(w.name)
            worker_keys = len([k for k in all_state if k.startswith(f"worker:{w.name}:")])
            result.append({
                "name": w.name,
                "role": w.role,
                "provider": w.provider,
                "model": w.model,
                "emoji": w.emoji,
                "status": w.status,
                "description": w.description,
                "task_count": w.task_count,
                "unread": unread,
                "memory_keys": worker_keys,
            })
        return result

    def stats(self) -> dict:
        return {
            "total_workers": len(self._workers),
            "idle": sum(1 for w in self._workers.values() if w.status == "idle"),
            "busy": sum(1 for w in self._workers.values() if w.status == "busy"),
            "error": sum(1 for w in self._workers.values() if w.status == "error"),
            "total_tasks": sum(w.task_count for w in self._workers.values()),
        }
