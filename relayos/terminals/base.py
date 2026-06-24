"""Base terminal adapter — wraps any AI CLI as a callable terminal."""
from __future__ import annotations

import logging
import shutil
import subprocess
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TerminalInstance:
    """A running terminal instance (one process, one session)."""
    id: str
    type: str          # "claude", "mimo", "opencode", "codex", "qcode"
    name: str          # user-given name, e.g. "claude-main"
    model: str         # current model
    status: str        # "idle", "busy", "error", "offline"
    pid: Optional[int] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_used: Optional[str] = None
    task_count: int = 0
    total_tokens: int = 0


@dataclass
class TerminalResult:
    content: str
    terminal_id: str
    type: str
    model: str
    exit_code: int = 0
    duration_ms: int = 0
    error: Optional[str] = None


class BaseTerminal(ABC):
    """Abstract base for wrapping CLI tools as terminals.

    Each terminal wraps one AI CLI tool (Claude Code, Mimo, etc.)
    and can spawn multiple independent instances.
    """

    type: str = ""
    binary: str = ""          # the CLI binary name, e.g. "claude"
    default_model: str = ""
    max_instances: int = 5     # default max concurrent instances

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        """Build the CLI command to execute.

        Returns a list of args for subprocess.run, e.g.
        ["claude", "-p", "your prompt"]
        """
        ...

    def run(self, instance: TerminalInstance, prompt: str, **kwargs) -> TerminalResult:
        """Execute the prompt on a terminal instance."""
        start = time.time()
        cmd = self.build_command(instance, prompt, **kwargs)

        env = self._build_env(instance)
        env.setdefault("CLI_COLOR", "0")

        try:
            result = subprocess.run(
                cmd,
                input=prompt if "{stdin}" in str(cmd) else None,
                capture_output=True,
                text=True,
                timeout=kwargs.get("timeout", 300),
                env=env,
            )
            duration = int((time.time() - start) * 1000)
            instance.last_used = datetime.now(timezone.utc).isoformat()
            instance.task_count += 1

            if result.returncode != 0:
                stderr = result.stderr.strip() or "unknown error"
                instance.status = "error" if kwargs.get("mark_error", True) else instance.status
                return TerminalResult(
                    content=result.stdout or stderr,
                    terminal_id=instance.id,
                    type=self.type,
                    model=instance.model,
                    exit_code=result.returncode,
                    duration_ms=duration,
                    error=stderr,
                )

            instance.status = "idle"
            content = result.stdout.strip()
            # Estimate tokens (rough: 4 chars = 1 token)
            instance.total_tokens += len(content) // 4
            return TerminalResult(
                content=content,
                terminal_id=instance.id,
                type=self.type,
                model=instance.model,
                exit_code=0,
                duration_ms=duration,
            )

        except subprocess.TimeoutExpired as e:
            # Kill the orphaned subprocess so it doesn't stay running
            try:
                e.process.kill()
                e.process.wait(timeout=5)
            except Exception:
                pass
            instance.status = "error"
            return TerminalResult(
                content="",
                terminal_id=instance.id,
                type=self.type,
                model=instance.model,
                exit_code=-1,
                duration_ms=int((time.time() - start) * 1000),
                error="Timeout exceeded",
            )
        except FileNotFoundError:
            instance.status = "offline"
            return TerminalResult(
                content="",
                terminal_id=instance.id,
                type=self.type,
                model=instance.model,
                exit_code=-1,
                error=f"Binary '{self.binary}' not found. Is it installed?",
            )
        except Exception as e:
            instance.status = "error"
            return TerminalResult(
                content="",
                terminal_id=instance.id,
                type=self.type,
                model=instance.model,
                exit_code=-1,
                duration_ms=int((time.time() - start) * 1000),
                error=str(e),
            )

    def check_available(self) -> bool:
        """Check if the CLI binary is installed."""
        return shutil.which(self.binary) is not None

    def _build_env(self, instance: TerminalInstance) -> dict:
        """Build environment variables for the subprocess."""
        env = dict(__import__("os").environ)
        if instance.model:
            model = instance.model
            # Remove conflicting env vars, then set the correct one
            for var in ["CLAUDE_MODEL", "OPENAI_MODEL", "ANTHROPIC_MODEL", "MODEL"]:
                env.pop(var, None)
            if self.type == "claude":
                env["CLAUDE_MODEL"] = model
            elif self.type in ("opencode", "codex"):
                env["OPENAI_MODEL"] = model
            else:
                env["MODEL"] = model
        return env
