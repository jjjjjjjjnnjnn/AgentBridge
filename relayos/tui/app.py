"""RelayOS Terminal UI — ccswitch-style AI workforce manager.

Usage:
    relay          # Open TUI (default command)
    relay workers  # List workers
    relay run      # Run workflow

Like htop for your AI team. No browser, no server, no Docker.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from relayos.core.worker import WorkerManager


def run_tui():
    """Start the TUI. Blocks until 'q' is pressed."""
    import threading

    wm = WorkerManager()
    start_time = time.time()
    running = True

    def check_keys():
        nonlocal running
        if sys.platform == "win32":
            import msvcrt
            while running:
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode("utf-8", errors="ignore").lower()
                    if key == "q":
                        running = False
                    elif key == "r":
                        pass  # refresh is automatic
                time.sleep(0.1)
        else:
            import select
            import termios
            import tty
            fd = sys.stdin.fileno()
            old = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                while running:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1).lower()
                        if key == "q":
                            running = False
                        elif key == "r":
                            pass
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old)

    key_thread = threading.Thread(target=check_keys, daemon=True)
    key_thread.start()

    with Live(auto_refresh=False, screen=True) as live:
        try:
            while running:
                layout = _build_layout(wm, start_time)
                live.update(layout)
                live.refresh()
                time.sleep(2)  # refresh every 2s
        except KeyboardInterrupt:
            pass

    # Clear screen on exit
    print("\033[2J\033[H", end="")


def _build_layout(wm: WorkerManager, start_time: float) -> Layout:
    """Build the main layout."""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["header"].update(_render_header(wm, start_time))
    layout["body"].update(_render_body(wm))
    layout["footer"].update(_render_footer(wm))
    return layout


def _render_header(wm: WorkerManager, start_time: float) -> Panel:
    """Top bar with system status."""
    stats = wm.stats()
    elapsed = int(time.time() - start_time)
    text = Text()
    text.append(" RelayOS ", style="bold blue")
    text.append(f" Workers: {stats['total_workers']} ", style="cyan")
    text.append(f" Idle: {stats['idle']} ", style="green")
    text.append(f" Busy: {stats['busy']} ", style="yellow")
    text.append(f" Tasks: {stats['total_tasks']} ", style="white")
    text.append(f" [{elapsed}s] ", style="dim white")
    return Panel(text, style="blue")


def _render_body(wm: WorkerManager) -> Layout:
    """Two-panel body: workers + sidebar."""
    body = Layout()
    body.split_row(
        Layout(name="workers", ratio=2),
        Layout(name="sidebar", ratio=1),
    )
    body["workers"].update(_render_worker_table(wm))
    body["sidebar"].update(_render_sidebar(wm))
    return body


def _render_worker_table(wm: WorkerManager) -> Panel:
    """Worker list like htop."""
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("Worker", width=16)
    table.add_column("Role", width=14)
    table.add_column("Status", width=10)
    table.add_column("Model", width=30)
    table.add_column("Tasks", justify="right", width=5)
    table.add_column("Inbox", justify="right", width=5)

    team = wm.get_team()
    for w in team:
        status_style = {"idle": "green", "busy": "yellow", "error": "red"}.get(w["status"], "white")
        s = w["status"]
        if w["status"] == "busy":
            s = "● busy"
        elif w["status"] == "idle":
            s = "○ idle"
        unread = str(w["unread"]) if w["unread"] else ""

        table.add_row(
            f"{w['emoji']} {w['name']}",
            w["role"],
            Text(s, style=status_style),
            f"{w['provider']}/{w['model']}",
            str(w["task_count"]),
            unread,
        )
    return Panel(table, title="[bold]Workers[/bold]", border_style="dim")


def _render_sidebar(wm: WorkerManager) -> Layout:
    """Sidebar with inbox and tips."""
    sb = Layout()
    sb.split_column(Layout(name="inbox", ratio=2), Layout(name="tips", ratio=1))
    sb["inbox"].update(_render_inbox(wm))
    sb["tips"].update(_render_tips())
    return sb


def _render_inbox(wm: WorkerManager) -> Panel:
    """Recent inbox messages."""
    lines = []
    team = wm.get_team()
    for w in team:
        if w["unread"]:
            lines.append(f"  {w['emoji']} {w['name']}: {w['unread']} tasks")
    if not lines:
        lines.append("  All inboxes clear")
    return Panel("\n".join(lines), title="[bold]Inbox[/bold]", border_style="dim")


def _render_tips() -> Panel:
    """Quick tips."""
    tips = Text()
    tips.append("\n").append(" Quick commands:", style="bold cyan")
    tips.append("\n").append("  relay worker create <name>", style="dim")
    tips.append("\n").append("  relay run workflow.yaml", style="dim")
    tips.append("\n").append("  relay inbox list <name>", style="dim")
    tips.append("\n").append("  relay serve (web UI)", style="dim")
    tips.append("\n").append("\n [q] quit | auto-refresh 2s", style="italic dim")
    return Panel(tips, title="[bold]Commands[/bold]", border_style="dim")


def _render_footer(wm: WorkerManager) -> Panel:
    """Status bar."""
    stats = wm.stats()
    text = Text()
    text.append(" STATUS: ", style="bold green")
    text.append(f"{stats['total_workers']} workers online", style="green")
    text.append("  |  ", style="dim")
    text.append("~/.relayos/  ", style="dim")
    text.append("  |  ", style="dim")
    text.append("[q] quit  [r] refresh", style="italic dim")
    return Panel(text, style="green", height=3)


# ── CLI entry point ─────────────────────────────────────────


def main():
    """Entry point for 'relay' command."""
    import argparse
    parser = argparse.ArgumentParser(description="RelayOS — AI Workforce Manager")
    parser.add_argument("command", nargs="?", default="ui", help="Command: ui, workers, run")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    args = parser.parse_args()

    if args.command in ("ui", "tui", ""):
        run_tui()
    elif args.command == "workers":
        wm = WorkerManager()
        team = wm.get_team()
        for w in team:
            print(f"{w['emoji']} {w['name']:<15} {w['role']:<14} {w['status']:<8} {w['provider']}")
    elif args.command == "inbox":
        from relayos.core.inbox import WorkerInbox
        inbox = WorkerInbox()
        stats = inbox.get_stats()
        print(f"Inbox: {stats['unread']} unread of {stats['total']} total")
        for worker, count in stats.get("per_worker", {}).items():
            print(f"  {worker}: {count}")
    else:
        # Try running as a CLI command
        from relayos.cli.main import cli
        import sys
        sys.argv = ["relay", args.command] + args.args
        cli()


if __name__ == "__main__":
    main()
