"""Terminal pool manager - create, track, and dispatch to terminals."""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from relayos.config import load_config
from relayos.memory.store import MemoryStore
from relayos.terminals import get_terminal_class, list_terminal_types
from relayos.terminals.base import BaseTerminal, TerminalInstance, TerminalResult

logger = logging.getLogger(__name__)


class TerminalPool:
    """Manages multiple terminal instances across different CLI types.

    Supports:
    - Multiple instances of the same type (e.g., 3 Claude Code terminals)
    - Per-instance model selection
    - Parallel execution across terminals
    - Persistence via SQLite
    """

    def __init__(self, config_path: Optional[str] = None, memory: Optional[MemoryStore] = None, db_path: str = "~/.relayos/terminals.db"):
        self._terminals: dict[str, TerminalInstance] = {}
        self._adapters: dict[str, BaseTerminal] = {}
        self._lock = threading.Lock()
        self._counter = 0
        self.memory = memory or MemoryStore("~/.relayos/memory.db")
        self._db_path = str(Path(db_path).expanduser())
        self._init_db()
        self._load_from_db()
        self._load_config(config_path)

    def _load_config(self, config_path: Optional[str] = None):
        """Load terminal definitions from config."""
        cfg = load_config(None if not config_path else config_path)
        for t_def in cfg.terminals:
            try:
                self.create(
                    type_name=t_def["type"],
                    name=t_def.get("name", t_def["type"]),
                    model=t_def.get("model"),
                    env=t_def.get("env", {}),
                )
            except Exception as e:
                logger.warning(f"Failed to create terminal '{t_def.get('name')}': {e}")

    def _init_db(self):
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS terminals (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    model TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'idle',
                    created_at TEXT NOT NULL,
                    last_used TEXT,
                    task_count INTEGER DEFAULT 0,
                    total_tokens INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def _load_from_db(self):
        with sqlite3.connect(self._db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM terminals ORDER BY created_at").fetchall()
        for row in rows:
            inst = TerminalInstance(
                id=row["id"], type=row["type"], name=row["name"], model=row["model"] or "",
                status=row["status"], created_at=row["created_at"], last_used=row["last_used"],
                task_count=row["task_count"] or 0, total_tokens=row["total_tokens"] or 0,
            )
            with self._lock:
                self._terminals[inst.id] = inst
                try:
                    cls = get_terminal_class(inst.type)
                    self._adapters[inst.id] = cls()
                except ValueError:
                    pass
                # Track counter
                parts = inst.id.rsplit("-", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    n = int(parts[1])
                    if n > self._counter:
                        self._counter = n

    def _save_to_db(self, inst: TerminalInstance):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO terminals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (inst.id, inst.type, inst.name, inst.model, inst.status,
                 inst.created_at, inst.last_used, inst.task_count, inst.total_tokens),
            )
            conn.commit()

    def _delete_from_db(self, terminal_id: str):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute("DELETE FROM terminals WHERE id = ?", (terminal_id,))
            conn.commit()

    def _next_id(self, type_name: str) -> str:
        with self._lock:
            self._counter += 1
            return f"{type_name}-{self._counter}"

    def create(
        self,
        type_name: str,
        name: Optional[str] = None,
        model: Optional[str] = None,
        env: Optional[dict] = None,
        config: Optional[dict] = None,
    ) -> TerminalInstance:
        """Create a new terminal instance."""
        cls = get_terminal_class(type_name)
        adapter = cls(config or {})
        terminal_id = self._next_id(type_name)

        inst = TerminalInstance(
            id=terminal_id,
            type=type_name,
            name=name or terminal_id,
            model=model or adapter.default_model,
            status="idle",
        )

        with self._lock:
            self._terminals[terminal_id] = inst
            self._adapters[terminal_id] = adapter

        self._save_to_db(inst)

        logger.info(f"Terminal '{inst.name}' ({terminal_id}) created - type={type_name}, model={inst.model}")
        return inst

    def get(self, terminal_id: str) -> Optional[TerminalInstance]:
        return self._terminals.get(terminal_id)

    def remove(self, terminal_id: str) -> bool:
        self._delete_from_db(terminal_id)
        with self._lock:
            if terminal_id in self._terminals:
                del self._terminals[terminal_id]
                self._adapters.pop(terminal_id, None)
                return True
            return False

    def list(self, type_filter: Optional[str] = None) -> list[TerminalInstance]:
        instances = list(self._terminals.values())
        if type_filter:
            instances = [t for t in instances if t.type == type_filter]
        return instances

    def run(self, terminal_id: str, prompt: str, **kwargs) -> TerminalResult:
        """Run a prompt on a specific terminal (thread-safe)."""
        with self._lock:
            inst = self.get(terminal_id)
            if not inst:
                return TerminalResult(
                    content="", terminal_id=terminal_id, type="", model="",
                    exit_code=-1, error=f"Terminal '{terminal_id}' not found",
                )
            adapter = self._adapters.get(terminal_id)
            if not adapter:
                return TerminalResult(
                    content="", terminal_id=terminal_id, type=inst.type, model=inst.model,
                    exit_code=-1, error=f"Adapter for '{terminal_id}' not found",
                )
            inst.status = "busy"

        result = adapter.run(inst, prompt, **kwargs)

        with self._lock:
            inst.status = "idle" if result.exit_code == 0 else "error"
            inst.last_used = datetime.now(timezone.utc).isoformat()
            inst.task_count += 1
            if result.content:
                inst.total_tokens += len(result.content) // 4
            self._save_to_db(inst)
        return result

    def run_on_type(self, type_name: str, prompt: str, **kwargs) -> TerminalResult:
        """Run on the first available terminal of a given type."""
        for inst in self.list(type_filter=type_name):
            if inst.status == "idle":
                return self.run(inst.id, prompt, **kwargs)

        # No idle terminal found -- create a new one automatically
        logger.info(f"No idle {type_name} terminal, creating one...")
        inst = self.create(type_name)
        return self.run(inst.id, prompt, **kwargs)

    def run_parallel(self, tasks: list[dict]) -> list[TerminalResult]:
        """Run multiple prompts in parallel across terminals.

        Each task: { "terminal_type": str, "prompt": str, "terminal_id": optional }
        """
        results = [None] * len(tasks)
        threads = []

        def worker(idx: int, task: dict):
            if task.get("terminal_id"):
                results[idx] = self.run(task["terminal_id"], task["prompt"])
            else:
                results[idx] = self.run_on_type(task.get("terminal_type", "claude"), task["prompt"])

        for i, task in enumerate(tasks):
            t = threading.Thread(target=worker, args=(i, task))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        return results

    def stats(self) -> dict:
        """Get aggregate statistics across all terminals."""
        types = {}
        total_tasks = 0
        total_tokens = 0
        idle = busy = error = 0

        for inst in self._terminals.values():
            types.setdefault(inst.type, 0)
            types[inst.type] += 1
            total_tasks += inst.task_count
            total_tokens += inst.total_tokens
            if inst.status == "idle":
                idle += 1
            elif inst.status == "busy":
                busy += 1
            else:
                error += 1

        return {
            "total": len(self._terminals),
            "idle": idle,
            "busy": busy,
            "error": error,
            "by_type": types,
            "total_tasks": total_tasks,
            "total_tokens_estimated": total_tokens,
        }

    def close_all(self):
        """Remove all terminals."""
        with self._lock:
            self._terminals.clear()
            self._adapters.clear()
