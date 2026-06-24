"""RelayOS Terminal UI — AI Control Panel.

Like htop for your AI team.
Switch profiles with one keypress.
See everything at a glance.

Windows: Keyboard works with standard keys (q, f, b, u, o, m, c, 1-9, r)
Mouse: Not supported in terminal TUI mode (use relayos CLI commands instead)
"""
from __future__ import annotations

import logging
import sys
import time
from pathlib import Path

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from relayos.core.worker import WorkerManager

logger = logging.getLogger(__name__)


def _getch_win() -> str:
    """Read one keypress on Windows using msvcrt."""
    import msvcrt
    import ctypes
    try:
        if not msvcrt.kbhit():
            return ""
        # Get the actual console code page (cp936 on Chinese Windows, cp437 on US)
        cp = ctypes.windll.kernel32.GetConsoleCP()
        raw = msvcrt.getch()
        # Handle extended key prefix (arrow keys, F-keys)
        if raw in (b'\xe0', b'\x00'):
            msvcrt.getch()  # consume the second byte
            return ""
        return raw.decode(f'cp{cp}').lower()
    except Exception:
        return ""


def _getch_unix() -> str:
    """Read one keypress on Unix/POSIX using termios."""
    import termios
    import tty
    import select
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        if select.select([sys.stdin], [], [], 0.05)[0]:
            return sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ""


def run_tui():
    """Run the TUI control panel."""
    wm = WorkerManager()
    start_time = time.time()
    current_profile = ["balanced"]
    selected = [0]
    running = True
    _getch = _getch_win if sys.platform == "win32" else _getch_unix

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )
    body = Layout()
    body.split_row(Layout(name="workers", ratio=3), Layout(name="panel", ratio=2))
    layout["body"].update(body)

    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while running:
                # Handle keyboard input (non-blocking)
                key = _getch()
                if key == "q":
                    running = False
                elif key == "f":
                    current_profile[0] = "free"
                    _save_profile("free")
                elif key == "b":
                    current_profile[0] = "balanced"
                    _save_profile("balanced")
                elif key == "u":
                    current_profile[0] = "quality"
                    _save_profile("quality")
                elif key == "o":
                    current_profile[0] = "opencode"
                    _save_profile("opencode")
                elif key == "m":
                    current_profile[0] = "mimo"
                    _save_profile("mimo")
                elif key == "c":
                    current_profile[0] = "claude"
                    _save_profile("claude")
                elif key in "123456789":
                    selected[0] = int(key) - 1

                # Rebuild layout
                stats = wm.stats()
                elapsed = int(time.time() - start_time)

                # Header
                t = Text()
                t.append(" RelayOS ", style="bold blue")
                t.append(f" Workers:{stats['total_workers']} ", style="cyan")
                t.append(f" Idle:{stats['idle']} ", style="green")
                t.append(f" Busy:{stats['busy']} ", style="yellow")
                t.append(f" Tasks:{stats['total_tasks']} ", style="white")
                t.append(f" [{elapsed}s] ", style="dim")
                t.append(f" Profile:{current_profile[0]} ", style="bold cyan")
                layout["header"].update(Panel(t, style="blue"))

                # Workers table
                table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
                table.add_column("#", width=2)
                table.add_column("Worker", width=14)
                table.add_column("Status", width=8)
                table.add_column("Model", width=28)
                table.add_column("Tasks", justify="right", width=5)
                team = wm.get_team()
                for i, w in enumerate(team):
                    sel_style = "reverse" if i == selected[0] else ""
                    s = w["status"]
                    ss = {"idle": "green", "busy": "yellow", "error": "red"}.get(s, "white")
                    label = f"● {s}" if s == "busy" else f"○ {s}" if s == "idle" else s
                    table.add_row(
                        str(i + 1) if i == selected[0] else " ",
                        f"{w['emoji']} {w['name']}",
                        Text(label, style=ss),
                        f"{w['provider']}/{w['model'][:20]}",
                        str(w["task_count"]),
                        style=sel_style,
                    )
                body["workers"].update(Panel(table, title="[bold]Workers (1-9 select)[/bold]", border_style="dim"))

                # Status panel
                lines = [f"  Profile: {current_profile[0]}"]
                # Cost
                try:
                    from relayos.cost import CostManager
                    r = CostManager().get_report()
                    if r["total_cost"] > 0:
                        lines.append(f"  Cost: ${r['total_cost']:.4f}")
                        for p, d in list(r.get("providers", {}).items())[:3]:
                            lines.append(f"    {p}: ${d['cost']:.4f}")
                    else:
                        lines.append("  Cost: $0.00")
                except Exception:
                    pass
                lines.append("")
                # Pending tasks
                try:
                    from relayos.core.state import StateStore
                    lines.append(f"  Pending tasks: {StateStore().inbox_count()}")
                except Exception:
                    pass
                body["panel"].update(Panel("\n".join(lines), title="[bold]Status[/bold]", border_style="dim"))

                # Footer
                t = Text()
                t.append(f" {stats['total_workers']}w {stats['idle']}i {stats['busy']}b", style="green")
                t.append("  |  ", style="dim")
                try:
                    from relayos.core.state import StateStore
                    ic = StateStore().inbox_count()
                    t.append(f"inbox:{ic}", style="yellow" if ic else "dim")
                except Exception:
                    t.append("inbox:-", style="dim")
                t.append("  |  ", style="dim")
                try:
                    from relayos.cost import CostManager
                    r = CostManager().get_report()
                    t.append(f"${r['total_cost']:.4f}", style="white" if r['total_cost'] > 0 else "dim")
                except Exception:
                    t.append("$0", style="dim")
                t.append("  |  ", style="dim")
                t.append(f"[{current_profile[0]}]", style="cyan")
                t.append("  |  ", style="dim")
                t.append("q=quit 1-9=select f=free b=bal u=quality o=opencode m=mimo c=claude", style="dim")
                layout["footer"].update(Panel(t, style="green", height=3))

                # Update display and wait
                live.refresh()
                # Short sleep to yield CPU while keeping responsiveness
                time.sleep(0.2)

        except KeyboardInterrupt:
            pass

    # Clean exit
    print("\033[2J\033[H", end="")


def _save_profile(profile: str):
    """Save profile preference to config file."""
    try:
        from relayos.config import get_config_dir
        import yaml
        p = get_config_dir() / "config.yaml"
        if p.exists():
            c = yaml.safe_load(p.read_text()) or {}
            c.setdefault("routing", {})["default"] = profile
            p.write_text(yaml.dump(c, default_flow_style=False), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Failed to save profile '{profile}': {e}")


def main():
    """Entry point for the relay command."""
    import sys as _sys
    import argparse
    p = argparse.ArgumentParser(description="RelayOS — AI Control Panel")
    p.add_argument("cmd", nargs="?", default="ui")
    p.add_argument("args", nargs="*")
    a = p.parse_args()

    # Piped input mode
    if not _sys.stdin.isatty() and a.cmd == "ui":
        msg = _sys.stdin.read().strip()
        if msg:
            from relayos.core.conversation import ConversationEngine
            eng = ConversationEngine()
            try:
                result = eng.chat(msg)
                _sys.stdout.write(result["content"])
            except Exception as e:
                _sys.stderr.write(f"[ERR] {e}\n")
                _sys.exit(1)
        return

    if a.cmd in ("ui", "tui", ""):
        run_tui()
    elif a.cmd == "workers":
        wm = WorkerManager()
        for w in wm.get_team():
            print(f"{w['emoji']} {w['name']:<15} {w['role']:<14} {w['status']:<8} {w['provider']}")
    else:
        from relayos.cli.main import cli as cli_main
        _sys.argv = ["relay", a.cmd] + a.args
        cli_main()


if __name__ == "__main__":
    main()
