"""RelayOS Terminal UI — Input-first Agent Workspace.

Usage:
  relay              → TUI workspace
  relay "task"       → Auto-dispatch directly

Keys: type + Enter to submit task, q=quit, s=settings, ?=help
"""
from __future__ import annotations

import logging
import sys
import time

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from relayos.core.session import SessionStore
from relayos.providers import detect_providers
from relayos.providers.router import ProviderRouter

logger = logging.getLogger(__name__)


def _getch() -> str:
    """Non-blocking single key. Returns '' if no key."""
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
                return sys.stdin.read(1).lower()
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception:
            pass
        return ""


# ── Auto-dispatch via ProviderRouter ───────────────────────────

def auto_dispatch(task: str, mode: str = "auto") -> dict:
    """Execute task through ProviderRouter."""
    from relayos.core.conversation import ConversationEngine
    from relayos.core.scheduler import ModelScheduler

    scheduler = ModelScheduler()
    task_type = scheduler.classify_task(task)

    eng = ConversationEngine()
    result = eng.chat(task)
    return {
        "type": "chat",
        "task": task,
        "content": result.get("content", ""),
        "worker": result.get("worker", ""),
        "model": result.get("model", ""),
        "session_id": result.get("session_id", ""),
    }


def _render_settings(router: ProviderRouter) -> str:
    """Build settings panel."""
    status = router.get_status()
    lines = [
        "  RelayOS Settings",
        "  " + "=" * 40,
        "",
        f"  Mode:  {'[AUTO]' if router.mode == 'auto' else '[EDIT]'}",
        "         auto = execute without asking",
        "         edit = ask before each call",
        f"  [M] Toggle mode",
        "",
        "  Providers:",
        "  " + "-" * 40,
    ]
    for p in status:
        avail = "●" if p["available"] else "○"
        en = "✓" if p["enabled"] else "✗"
        lines.append(f"  {avail} {en} {p['name']:<20} {p['type']:<5} {p['weight']:>3}%  [{p['id']}]")
    lines.append("")
    lines.append("  [E]nable/disable  [W]eight  [Back: B or Esc]")
    return "\n".join(lines)


def run_tui(initial_task: str = ""):
    """Run the TUI workspace."""
    from relayos.config import get_config_dir

    ss = SessionStore()
    router = ProviderRouter()
    start_time = time.time()

    # State
    mode = "input"       # input | results | settings
    input_buffer = list(initial_task)
    output_lines: list[str] = []
    result_data: dict = {}
    config_exists = (get_config_dir() / "config.yaml").exists()

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
                key = _getch()

                if mode == "settings":
                    if key in ("b", "q", "\x1b"):
                        mode = "input"
                    elif key == "m":
                        router.mode = "edit" if router.mode == "auto" else "auto"
                    elif key == "e":
                        pass  # toggle enable for selected (advance feature)

                elif mode == "input":
                    if key == "q":
                        break
                    elif key == "s":
                        mode = "settings"
                        continue
                    elif key == "?":
                        output_lines = [
                            "  RelayOS Help",
                            "  " + "=" * 40,
                            "",
                            "  Type your task, press Enter to execute.",
                            "  The system auto-routes to the best provider.",
                            "",
                            "  Keys:",
                            "    Enter   Submit task",
                            "    q       Quit",
                            "    s       Settings (providers, mode)",
                            "    ?       This help",
                            "    n       New task (after results)",
                            "",
                            "  Providers:",
                            "    API:  OpenAI, Anthropic, Google, DeepSeek",
                            "    CLI:  claude, opencode, mimo (auto-detected)",
                            "",
                            "  Modes:",
                            "    auto    Execute without asking",
                            "    edit    Ask before each provider call",
                        ]
                    elif key == "\r" or key == "\n":
                        task_text = "".join(input_buffer).strip()
                        if task_text:
                            output_lines = [f"  Processing: {task_text}"]
                            try:
                                result_data = auto_dispatch(task_text, router.mode)
                                output_lines = [f"  ✓ {result_data.get('task', '')}"]
                                worker = result_data.get("worker", "")
                                model = result_data.get("model", "")
                                content = result_data.get("content", "")
                                if worker:
                                    output_lines.append(f"  [{worker} ({model})]")
                                output_lines.append(f"  {content[:800]}")
                                sid = result_data.get("session_id", "")
                                if sid:
                                    output_lines.append(f"")
                                    output_lines.append(f"  Session: {sid}")
                            except Exception as e:
                                output_lines = [f"  [ERR] {e}"]
                            mode = "results"
                        input_buffer = []
                    elif key == "\x7f" or key == "\b" or key == "\x08":
                        if input_buffer:
                            input_buffer.pop()
                    elif key == "\x1b":
                        input_buffer = []
                    elif key and len(key) == 1 and key.isprintable():
                        input_buffer.append(key)

                elif mode == "results":
                    if key == "n":
                        mode = "input"
                        input_buffer = []
                        output_lines = []
                        result_data = {}
                    elif key == "s":
                        mode = "settings"
                    elif key == "q":
                        break
                    elif key == "?":
                        output_lines.append("")
                        output_lines.append("  [n] new task  [s] settings  [q] quit")

                # ── Render ──
                elapsed = int(time.time() - start_time)

                # Header
                h = Text()
                h.append(" RelayOS ", style="bold blue")
                h.append(f" {router.mode.upper()} ", style="yellow" if router.mode == "edit" else "green")
                h.append(f" [{elapsed}s]", style="dim")
                if config_exists:
                    h.append(" ✓cfg", style="green")
                layout["header"].update(Panel(h, style="blue"))

                # Body
                body_lines = []

                if mode == "settings":
                    body_lines.append(_render_settings(router))
                elif mode == "results" and output_lines:
                    body_lines.extend(output_lines)
                elif mode == "input":
                    # Recent conversations
                    recent = ss.list_sessions(limit=5)
                    if recent:
                        body_lines.append("  [Recent Conversations]")
                        for s in recent:
                            name = s.get("name", "?")[:30]
                            age = s.get("updated_at", 0)
                            if age:
                                mins = int((time.time() - age) / 60)
                                ago = f"{mins}min ago" if mins < 120 else f"{mins//60}hr ago"
                                body_lines.append(f"    {name:<34} {ago}")
                        body_lines.append("")

                    # Input line
                    input_str = "".join(input_buffer)
                    body_lines.append(f"  > {input_str}█")
                    body_lines.append("")
                    if not input_buffer:
                        body_lines.append("  Type your task and press Enter.")
                        # Show detected providers
                        providers = detect_providers()
                        available = [p for p in providers if p.enabled]
                        if available:
                            names = ", ".join(p.display_name for p in available[:4])
                            body_lines.append(f"  Providers: {names}")
                else:
                    body_lines.append("  > _  [n] new task  [q] quit")

                layout["body"].update(Panel("\n".join(body_lines), border_style="dim"))

                # Footer
                f = Text()
                if mode == "settings":
                    f.append(" [B]ack  [M]ode  [Q]uit", style="dim")
                elif mode == "input":
                    f.append(" Enter=submit  s=settings  ?=help  q=quit", style="dim")
                elif mode == "results":
                    f.append(" [n] new task  [s] settings  [q] quit", style="dim")
                layout["footer"].update(Panel(f, style="green", height=3))

                live.refresh()
                time.sleep(0.05)

        except KeyboardInterrupt:
            pass

    print("\033[2J\033[H", end="")


def main():
    """Entry for `relay` command.

    relay          → TUI workspace
    relay "task"   → Execute directly
    """
    import argparse
    p = argparse.ArgumentParser(description="RelayOS — Agent Workspace")
    p.add_argument("cmd", nargs="?")
    p.add_argument("args", nargs="*")
    a = p.parse_args()

    if not sys.stdin.isatty() and not a.cmd:
        task = sys.stdin.read().strip()
        if task:
            run_tui(initial_task=task)
        return

    if a.cmd and a.cmd not in ("ui", "tui", ""):
        task = a.cmd
        if a.args:
            task += " " + " ".join(a.args)
        try:
            result = auto_dispatch(task)
            print(f"\n[{result.get('worker','')} ({result.get('model','')})]")
            print(result.get("content", ""))
            print(f"\nSession: {result.get('session_id','')}")
        except Exception as e:
            print(f"[ERR] {e}", file=sys.stderr)
            sys.exit(1)
        return

    run_tui()


if __name__ == "__main__":
    main()
