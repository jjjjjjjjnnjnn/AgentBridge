"""Real-time terminal display for workflow execution.

Provides animated spinners, step status tracking, and compact output
for CLI workflow runs. No external dependencies — uses ANSI escape codes.
"""
from __future__ import annotations

import itertools
import shutil
import sys
import threading
import time
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Optional

SPINNER_CHARS = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
PASS_CHAR = "✓"
FAIL_CHAR = "✗"
WARN_CHAR = "⚠"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%H:%M:%S")


class StepDisplay:
    """Tracks and displays one workflow step."""

    def __init__(self, index: int, agent: str, prompt: str):
        self.index = index
        self.agent = agent
        self.prompt = prompt[:50] + "..." if len(prompt) > 50 else prompt
        self.status = "pending"  # pending | running | done | error
        self.model = ""
        self.duration_ms = 0
        self.char_count = 0


class WorkflowDisplay:
    """Animated multi-step display for workflow execution.

    Shows all steps with live spinners, updates in-place using ANSI codes.
    Supports parallel and sequential execution visualization.
    """

    def __init__(self, workflow_name: str):
        self.workflow_name = workflow_name
        self.steps: list[StepDisplay] = []
        self._lock = threading.Lock()
        self._spinner_gen = itertools.cycle(SPINNER_CHARS)
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._start_time = time.time()
        self._width = min(shutil.get_terminal_size().columns, 100)

    def add_step(self, agent: str, prompt: str) -> int:
        """Add a step and return its index."""
        idx = len(self.steps)
        self.steps.append(StepDisplay(idx, agent, prompt))
        return idx

    def set_running(self, step_idx: int):
        with self._lock:
            if step_idx < len(self.steps):
                self.steps[step_idx].status = "running"

    def set_done(self, step_idx: int, model: str = "", duration_ms: int = 0, chars: int = 0):
        with self._lock:
            if step_idx < len(self.steps):
                s = self.steps[step_idx]
                s.status = "done"
                s.model = model
                s.duration_ms = duration_ms
                s.char_count = chars

    def set_error(self, step_idx: int, error: str = ""):
        with self._lock:
            if step_idx < len(self.steps):
                self.steps[step_idx].status = "error"

    def _render(self) -> str:
        """Build the display frame."""
        elapsed = int(time.time() - self._start_time)
        lines = [f" RelayOS  |  {self.workflow_name}  |  {elapsed}s"]

        with self._lock:
            for s in self.steps:
                spinner = next(self._spinner_gen) if s.status == "running" else " "
                if s.status == "pending":
                    prefix = "  "
                    color = "\033[90m"  # gray
                    suffix = ""
                elif s.status == "running":
                    prefix = f" {spinner}"
                    color = "\033[94m"  # blue
                    suffix = ""
                elif s.status == "done":
                    prefix = f" {PASS_CHAR}"
                    color = "\033[92m"  # green
                    dur = f"{s.duration_ms / 1000:.1f}s" if s.duration_ms else ""
                    chars = f" {s.char_count}c" if s.char_count else ""
                    model = f" [{s.model}]" if s.model else ""
                    suffix = f"{color}{dur}{chars}{model}\033[0m"
                else:
                    prefix = f" {FAIL_CHAR}"
                    color = "\033[91m"  # red
                    suffix = ""

                line = f"{color}{prefix}\033[0m {s.agent:<12} {s.prompt[:self._width - 30]}"
                if suffix:
                    line += f" {suffix}"
                lines.append(line)

        total_done = sum(1 for s in self.steps if s.status == "done")
        total_err = sum(1 for s in self.steps if s.status == "error")
        status_line = f"  [{total_done}/{len(self.steps)} completed"
        if total_err:
            status_line += f", {total_err} errors"
        status_line += "]"
        lines.append(status_line)

        return "\n".join(lines)

    def start(self):
        """Begin the animation thread."""
        self._running = True
        self._start_time = time.time()
        self._thread = threading.Thread(target=self._animate, daemon=True)
        self._thread.start()

    def _animate(self):
        """Continuously redraw while running."""
        while self._running and any(s.status in ("pending", "running") for s in self.steps):
            frame = self._render()
            sys.stderr.write("\033[?25l")  # hide cursor
            sys.stderr.write("\033[J")  # clear below
            sys.stderr.write(frame)
            sys.stderr.write("\033[?25h")  # show cursor
            sys.stderr.flush()
            time.sleep(0.08)

        # Final render
        final = self._render()
        sys.stderr.write("\033[?25l")
        sys.stderr.write("\033[J")
        sys.stderr.write(final)
        sys.stderr.write("\033[?25h")
        sys.stderr.write("\n")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
