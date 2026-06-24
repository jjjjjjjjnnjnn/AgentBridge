"""RelayOS Terminal UI — Clean input-first workspace.

Usage:
  relay              → Open TUI workspace
  relay "task"       → Auto-dispatch task, show progress

The TUI is a focused workspace with:
  - Top: status bar
  - Center: conversation / progress
  - Bottom: input line + shortcuts

No config required. Auto-detects installed AI CLIs.
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from relayos.core.worker import WorkerManager
from relayos.core.session import SessionStore
from relayos.terminals.scheduler import get_installed_terminals, TERMINAL_CAPABILITIES

logger = logging.getLogger(__name__)


# ── Keyboard input (cross-platform) ────────────────────────────

def _getch() -> str:
    """Non-blocking single key read. Returns '' if no key."""
    if sys.platform == "win32":
        import msvcrt, ctypes
        try:
            if not msvcrt.kbhit():
                return ""
            cp = ctypes.windll.kernel32.GetConsoleCP()
            raw = msvcrt.getch()
            if raw in (b'\xe0', b'\x00'):
                msvcrt.getch()
                return ""
            return raw.decode(f'cp{cp}').lower()
        except Exception:
            return ""
    else:
        import termios, tty, select
        try:
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            tty.setraw(fd)
            if select.select([sys.stdin], [], [], 0.05)[0]:
                ch = sys.stdin.read(1)
                return ch.lower()
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass
        return ""


def _getch_blocking() -> str:
    """Blocking single key read. Waits until a key is pressed."""
    if sys.platform == "win32":
        import msvcrt, ctypes
        try:
            cp = ctypes.windll.kernel32.GetConsoleCP()
            raw = msvcrt.getch()
            if raw in (b'\xe0', b'\x00'):
                msvcrt.getch()
                return ""
            return raw.decode(f'cp{cp}').lower()
        except Exception:
            return ""


# ── Auto-dispatch ──────────────────────────────────────────────

def auto_dispatch(task: str) -> dict:
    """Auto-detect intent and execute task.

    Routes to appropriate worker(s) based on task content.
    """
    from relayos.core.conversation import ConversationEngine
    from relayos.core.scheduler import ModelScheduler

    scheduler = ModelScheduler()
    task_type = scheduler.classify_task(task)

    eng = ConversationEngine()

    if task_type in ("architecture", "research", "review"):
        # Multi-worker: use group chat
        participants = ["researcher", "architect", "coder", "reviewer"]
        result = eng.group_chat(task, participants=participants)
        return {
            "type": "group",
            "task": task,
            "responses": result["responses"],
            "session_id": result["session_id"],
        }
    else:
        # Single worker chat
        result = eng.chat(task)
        return {
            "type": "chat",
            "task": task,
            "content": result["content"],
            "worker": result["worker"],
            "model": result["model"],
            "session_id": result["session_id"],
        }


# ── TUI ────────────────────────────────────────────────────────

def run_tui(initial_task: str = ""):
    """Run the TUI workspace.

    Args:
        initial_task: If provided, auto-execute on startup.
    """
    from relayos.core.conversation import ConversationEngine
    from relayos.config import get_config_dir

    wm = WorkerManager()
    ss = SessionStore()
    start_time = time.time()
    config_exists = (get_config_dir() / "config.yaml").exists()

    # State
    mode = "input"       # input | working | done
    input_buffer = list(initial_task)
    output_lines: list[str] = []
    sessions_list = ss.list_sessions(limit=10)
    installed_terms = get_installed_terminals()
    recent_sessions = ss.list_sessions(limit=10)

    # Layout
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )

    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                # ── Handle key input ──
                key = _getch()

                if mode == "input":
                    if key == "q":
                        break
                    elif key == "\r" or key == "\n":
                        # Submit — process the task
                        task_text = "".join(input_buffer).strip()
                        if task_text:
                            mode = "working"
                            output_lines = [f"  Processing: {task_text}"]
                            # Execute in background
                            try:
                                result = auto_dispatch(task_text)
                                output_lines = [f"  ✓ {result['task']}"]
                                if result["type"] == "chat":
                                    output_lines.append(f"  [{result['worker']} ({result.get('model','')})]")
                                    output_lines.append(f"  {result['content'][:500]}")
                                else:
                                    for r in result.get("responses", []):
                                        worker = r.get("worker", "?")
                                        content = r.get("content", "")[:200]
                                        output_lines.append(f"  [{worker}] {content}")
                                output_lines.append("")
                                output_lines.append(f"  Session: {result.get('session_id','')}")
                            except Exception as e:
                                output_lines = [f"  [ERR] {e}"]
                            mode = "done"
                        input_buffer = []
                    elif key == "\x7f" or key == "\b" or key == "\x08":  # Backspace (Unix/Windows)
                        if input_buffer:
                            input_buffer.pop()
                    elif key == "\x1b":  # Escape
                        input_buffer = []
                    elif key and len(key) == 1 and key.isprintable():
                        input_buffer.append(key)

                elif mode == "done":
                    if key == "n":
                        # New task
                        mode = "input"
                        input_buffer = []
                        output_lines = []
                    elif key == "q":
                        break
                    elif key == "h":
                        mode = "input"
                        input_buffer = []
                        output_lines = []
                        sessions_list = ss.list_sessions(limit=10)

                # ── Build display ──

                # Header
                elapsed = int(time.time() - start_time)
                stats = wm.stats()

                header_parts = [(" RelayOS ", "bold blue")]
                if initial_task:
                    header_parts.append((f" running...", "yellow"))
                else:
                    header_parts.append((f" {stats['total_workers']}w ", "cyan"))
                    header_parts.append((f" {elapsed}s", "dim"))
                if config_exists:
                    header_parts.append((f" ✓cfg", "green"))
                h = Text.assemble(*header_parts)
                layout["header"].update(Panel(h, style="blue"))

                # Body
                body_lines = []

                if mode == "input" or mode == "done":
                    if sessions_list and mode == "input":
                        body_lines.append("  [Recent Conversations]")
                        for s in sessions_list[:5]:
                            name = s.get("name", "?")[:30]
                            ts = s.get("updated_at", 0)
                            ago = f"{int((time.time() - ts) / 60)}min ago" if ts else ""
                            body_lines.append(f"    {name:<32} {ago}")
                        body_lines.append("")

                if mode == "working":
                    body_lines.append("  Working...")
                    body_lines.append("  Task: " + "".join(input_buffer) if input_buffer else "")

                if output_lines:
                    body_lines.extend(output_lines)

                if not body_lines:
                    body_lines.append("")
                    body_lines.append("  Type your task below and press Enter.")
                    if installed_terms:
                        body_lines.append(f"  Detected: {', '.join(installed_terms)}")
                    body_lines.append("")

                # Input line
                input_str = "".join(input_buffer)
                if mode == "input":
                    body_lines.append(f"  > {input_str}█")
                elif mode == "done":
                    body_lines.append(f"  > _  [n] new task  [q] quit")

                layout["body"].update(Panel("\n".join(body_lines), border_style="dim"))

                # Footer
                f = Text()
                if mode == "input":
                    f.append(" Type your task, press Enter to execute", style="dim")
                    f.append("  |  ", style="dim")
                    f.append("q=quit", style="dim")
                elif mode == "done":
                    f.append(" [n] New task", style="bold")
                    f.append("  |  ", style="dim")
                    f.append("[q] Quit", style="dim")
                else:
                    f.append(" Working...", style="yellow")
                layout["footer"].update(Panel(f, style="green", height=3))

                live.refresh()
                time.sleep(0.05)

        except KeyboardInterrupt:
            pass

    print("\033[2J\033[H", end="")


def main():
    """Entry for `relay` command.

    relay          → Open TUI workspace
    relay "task"   → Execute task, show output
    """
    import argparse

    p = argparse.ArgumentParser(description="RelayOS — Agent Workspace")
    p.add_argument("cmd", nargs="?")
    p.add_argument("args", nargs="*")
    a = p.parse_args()

    # Piped input: echo "task" | relay
    if not sys.stdin.isatty() and not a.cmd:
        task = sys.stdin.read().strip()
        if task:
            run_tui(initial_task=task)
        return

    # relay "task" — auto-dispatch directly
    if a.cmd and a.cmd not in ("ui", "tui", ""):
        task = a.cmd
        if a.args:
            task += " " + " ".join(a.args)
        try:
            result = auto_dispatch(task)
            if result["type"] == "chat":
                print(f"\n[{result['worker']} ({result.get('model','')})]")
                print(result["content"])
            else:
                for r in result.get("responses", []):
                    print(f"\n[{r.get('worker','?')}]")
                    print(f"  {r.get('content','')[:500]}")
            print(f"\nSession: {result.get('session_id','')}")
        except Exception as e:
            print(f"[ERR] {e}", file=sys.stderr)
            sys.exit(1)
        return

    # relay (no args) — open TUI
    run_tui()


if __name__ == "__main__":
    main()
