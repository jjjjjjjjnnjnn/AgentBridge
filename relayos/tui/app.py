"""RelayOS Terminal UI — AI Agent Workspace.

3-panel layout: Navigation | Workspace | Context

Keyboard shortcuts:
  n    New conversation
  r    Recent conversations
  i    Integrate conversations
  g    Conversation graph
  k    Knowledge view
  w    Workers view
  p    Project settings
  ?    Help
  q    Quit
  1-9  Select conversation
  a    Architect worker
  c    Coder worker
  v    Reviewer worker
  d    Debugger worker
  f    Free profile
  b    Balanced profile
  u    Quality profile
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
from rich.box import MINIMAL

from relayos.core.worker import WorkerManager
from relayos.core.session import SessionStore

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# Keyboard Input (cross-platform)
# ═══════════════════════════════════════════════════════════════

def _getch_win() -> str:
    """Read one keypress on Windows. Returns empty string if no key."""
    import msvcrt
    import ctypes
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


def _getch_unix() -> str:
    """Read one keypress on Unix. Returns empty string if no key."""
    import termios, tty, select
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        if select.select([sys.stdin], [], [], 0.05)[0]:
            return sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ""


# ═══════════════════════════════════════════════════════════════
# Renderers
# ═══════════════════════════════════════════════════════════════

def _render_welcome() -> Panel:
    """Render the welcome/home screen with auto-detected terminals."""
    from relayos.terminals.scheduler import get_installed_terminals, TERMINAL_CAPABILITIES
    installed = get_installed_terminals()

    t = Text()
    t.append("\n")
    t.append("  RelayOS\n", style="bold blue")
    t.append("  Agent Operating System — Integrated Terminal Workspace\n", style="dim")
    t.append("\n")

    # Show detected terminals
    if installed:
        t.append("  Detected AI Terminals:\n", style="bold green")
        for term in installed:
            caps = TERMINAL_CAPABILITIES.get(term, {})
            best = sorted(caps.items(), key=lambda x: -x[1])[:3]
            strengths = ", ".join(f"{k}={v}" for k, v in best if k != "cost")
            t.append(f"    [{term}] {strengths}\n", style="cyan")
        t.append("\n")
    else:
        t.append("  No AI CLI terminals detected.\n", style="yellow")
        t.append("  Install: opencode, mimo, or claude\n", style="dim")
        t.append("  Or add API keys in config\n", style="dim")
        t.append("\n")

    t.append("  [N] New Conversation    [R] Recent\n", style="bold")
    t.append("  [I] Integrate           [G] Graph\n", style="bold")
    t.append("  [?] Help                [Q] Quit\n", style="dim")
    t.append("\n")
    t.append("  Workers: [A]rchitect [C]oder [R]esearch [V]iew\n", style="dim")
    t.append("  Profile: [F]ree [B]alanced [U]uality\n", style="dim")
    return Panel(t, title="[bold]Welcome[/bold]", border_style="blue")


def _render_help() -> Panel:
    """Render the help/cheatsheet panel."""
    lines = [
        "  ┌─ Navigation ───────────────────────────┐",
        "  │ n  New Conversation                     │",
        "  │ r  Recent Conversations                 │",
        "  │ i  Integrate Conversations              │",
        "  │ g  Conversation Graph                   │",
        "  │ k  Knowledge View                       │",
        "  │ w  Workers View                         │",
        "  │ p  Project Settings                     │",
        "  │ ?  This Help                            │",
        "  │ q  Quit                                 │",
        "  ├─ Workers ───────────────────────────────┤",
        "  │ a  Architect     c  Coder               │",
        "  │ v  Reviewer      d  Debugger            │",
        "  ├─ Profiles ──────────────────────────────┤",
        "  │ f  Free         b  Balanced             │",
        "  │ u  Quality      o  OpenCode             │",
        "  │ m  Mimo         c  Claude               │",
        "  ├─ Chat Commands ─────────────────────────┤",
        "  │ /new     New conversation               │",
        "  │ /fork    Fork current conversation      │",
        "  │ /merge   Merge conversations            │",
        "  │ /attach  Attach conversation            │",
        "  │ /group   Multi-worker discussion        │",
        "  │ /sum     Summarize current              │",
        "  │ /know    Save as knowledge              │",
        "  └─────────────────────────────────────────┘",
    ]
    t = Text("\n".join(lines))
    return Panel(t, title="[bold]Help & Shortcuts[/bold]", border_style="green")


def _render_left_panel(sessions: list[dict], selected_idx: int, current_view: str) -> Panel:
    """Left panel: conversation list + navigation commands."""
    # Navigation commands at top
    nav = Text()
    nav.append("  [n] New   [r] Recent   [i] Integrate\n", style="bold cyan")
    nav.append("  [g] Graph [k] Knowledge [w] Workers\n", style="dim")
    nav.append("  [?] Help\n", style="dim")
    nav.append("\n")

    # Conversation list
    nav.append("Conversations\n", style="bold underline")
    nav.append("\n")

    if not sessions:
        nav.append("  No conversations yet\n", style="dim")
        nav.append("  Press [n] to start\n", style="dim")
    else:
        for i, s in enumerate(sessions[:9]):  # Show max 9 (keys 1-9)
            prefix = f"  {i+1}" if i < 9 else "   "
            if i == selected_idx:
                prefix = " >" + prefix[1:]
                style = "reverse"
            else:
                style = ""
            name = s.get("name", "?" )[:22]
            msg_count = s.get("msg_count", 0)
            mode = s.get("mode", "chat")[:1]
            line = f"{prefix} [{mode}] {name:<22} {msg_count}msgs"
            nav.append(line + "\n", style=style)

    return Panel(nav, title="[bold]Navigation[/bold]", border_style="dim", height=None)


def _render_workspace(current_view: str, selected_idx: int,
                      sessions: list[dict], messages: list,
                      team: list[dict]) -> Panel:
    """Center panel: chat area or welcome/help screen."""
    if current_view == "help":
        return _render_help()
    if current_view == "welcome":
        return _render_welcome()

    # Chat view
    if sessions and 0 <= selected_idx < len(sessions):
        conv = sessions[selected_idx]
        lines = [f"  {conv.get('name', '')}"]
        lines.append(f"  {'='*40}")
        lines.append("")
        if messages:
            for m in messages[-20:]:  # Last 20 messages
                role = m.get("role", "?")
                worker = m.get("from_worker", m.get("from", ""))
                content = m.get("content", "")
                preview = content[:200].replace("\n", " ")
                prefix = "  →" if role == "user" else "  ←"
                lines.append(f"{prefix} {worker:<12} {preview[:80]}")
                lines.append("")
        else:
            lines.append("  No messages yet.")
            lines.append("  Type /chat <message> to start.")
        return Panel("\n".join(lines), title=f"[bold]Chat: {conv.get('name', '')}[/bold]",
                     border_style="blue")

    return _render_welcome()


def _render_context_panel(current_profile: str, team: list[dict],
                          start_time: float, selected_worker_idx: int) -> Panel:
    """Right panel: context info (project, workers, budget, memory)."""
    # Project info
    parts = [f"  Profile: {current_profile}"]

    # Workers
    parts.append("")
    parts.append(" Workers")
    parts.append(" " + "-"*20)
    worker_keys = {"a": 0, "c": 1, "r": 2, "v": 3, "d": 4}
    for i, w in enumerate(team):
        marker = "●" if i == selected_worker_idx else "○"
        status_dot = {"idle": "·", "busy": "●", "error": "×"}.get(w["status"], "·")
        parts.append(f"  {marker} {status_dot} {w['emoji']} {w['name']:<12} {w['status']}")
    parts.append("")

    # Budget/Stats
    try:
        from relayos.cost import CostManager
        r = CostManager().get_report()
        cost_str = f"  Cost: ${r['total_cost']:.4f}"
        parts.append(cost_str)
    except Exception:
        parts.append("  Cost: $0.00")

    try:
        from relayos.core.state import StateStore
        ic = StateStore().inbox_count()
        parts.append(f"  Pending: {ic}")
    except Exception:
        pass

    parts.append(f"  Uptime: {int(time.time() - start_time)}s")
    parts.append("")
    parts.append(" [A]rchitect [C]oder")
    parts.append(" [R]esearch [V]iewer [D]ebugger")

    return Panel("\n".join(parts), title="[bold]Context[/bold]", border_style="dim")


def _render_footer(profile: str, team: list[dict]) -> Panel:
    """Compact status bar at bottom."""
    stats = {"total": len(team), "idle": 0, "busy": 0}
    for w in team:
        s = w["status"]
        if s in stats:
            stats[s] += 1
    t = Text()
    t.append(f" {stats['total']}w {stats['idle']}i {stats['busy']}b", style="green")
    t.append("  |  ", style="dim")
    try:
        from relayos.cost import CostManager
        r = CostManager().get_report()
        t.append(f"${r['total_cost']:.4f}", style="white" if r['total_cost'] > 0 else "dim")
    except Exception:
        t.append("$0", style="dim")
    t.append("  |  ", style="dim")
    t.append(f"[{profile}]", style="cyan")
    t.append("  |  ", style="dim")
    t.append("n=new r=rec i=int g=graph k=know w=wrk ?=help q=quit", style="dim")
    return Panel(t, style="green", height=3)


# ═══════════════════════════════════════════════════════════════
# Main TUI Loop
# ═══════════════════════════════════════════════════════════════

def run_tui():
    """Run the TUI workspace."""
    wm = WorkerManager()
    ss = SessionStore()
    _getch = _getch_win if sys.platform == "win32" else _getch_unix

    # State
    start_time = time.time()
    current_profile = "balanced"
    current_view = "welcome"       # welcome | chat | help | graph | workers
    selected_idx = 0               # selected conversation index
    selected_worker = 0            # selected worker index

    # Build layout skeleton (once)
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )
    body = Layout()
    body.split_row(
        Layout(name="left", ratio=2),
        Layout(name="center", ratio=5),
        Layout(name="right", ratio=2),
    )
    layout["body"].update(body)

    with Live(layout, refresh_per_second=4, screen=True) as live:
        try:
            while True:
                # ── Handle input ──
                key = _getch()
                if key == "q":
                    break
                elif key == "?":
                    current_view = "help" if current_view != "help" else "welcome"
                elif key == "n":
                    current_view = "chat"
                    # Create a new conversation
                    import uuid
                    name = f"Conv-{uuid.uuid4().hex[:6]}"
                    sess = ss.create_session(name)
                    selected_idx = 0
                elif key == "r":
                    current_view = "welcome"
                elif key == "i":
                    current_view = "graph"
                elif key == "w":
                    current_view = "workers"
                elif key == "g":
                    current_view = "graph"
                elif key == "k":
                    current_view = "welcome"
                elif key and key.isdigit() and "1" <= key <= "9":
                    selected_idx = int(key) - 1
                    if current_view in ("welcome",):
                        current_view = "chat"
                # Workers
                elif key == "a":
                    selected_worker = 0
                elif key == "c":
                    selected_worker = 1
                elif key == "v":
                    selected_worker = 3
                elif key == "d":
                    selected_worker = 4
                # Profiles
                elif key == "f":
                    current_profile = "free"
                    _save_profile("free")
                elif key == "b":
                    current_profile = "balanced"
                    _save_profile("balanced")
                elif key == "u":
                    current_profile = "quality"
                    _save_profile("quality")

                # ── Fetch data ──
                team = wm.get_team()
                sessions = ss.list_sessions(limit=20)

                # Get messages for selected conversation
                messages = []
                if sessions and 0 <= selected_idx < len(sessions):
                    conv = sessions[selected_idx]
                    msg_list = ss.get_messages(conv["id"], limit=30)
                    messages = [m.to_dict() for m in msg_list]
                else:
                    selected_idx = 0

                # ── Render ──
                # Header
                stats = wm.stats()
                elapsed = int(time.time() - start_time)
                h = Text()
                h.append(" RelayOS ", style="bold blue")
                h.append(f" Workers:{stats['total_workers']} ", style="cyan")
                h.append(f" Tasks:{stats['total_tasks']} ", style="white")
                h.append(f" [{elapsed}s] ", style="dim")
                h.append(f" Profile:{current_profile} ", style="bold cyan")
                layout["header"].update(Panel(h, style="blue"))

                # Left panel
                layout["left"].update(
                    _render_left_panel(sessions, selected_idx, current_view)
                )

                # Center panel
                layout["center"].update(
                    _render_workspace(current_view, selected_idx, sessions, messages, team)
                )

                # Right panel
                layout["right"].update(
                    _render_context_panel(current_profile, team, start_time, selected_worker)
                )

                # Footer
                layout["footer"].update(_render_footer(current_profile, team))

                # Refresh
                live.refresh()
                time.sleep(0.2)

        except KeyboardInterrupt:
            pass

    print("\033[2J\033[H", end="")


def _save_profile(profile: str):
    """Save profile to config."""
    try:
        from relayos.config import get_config_dir
        import yaml
        p = get_config_dir() / "config.yaml"
        if p.exists():
            c = yaml.safe_load(p.read_text()) or {}
            c.setdefault("routing", {})["default"] = profile
            p.write_text(yaml.dump(c, default_flow_style=False), encoding="utf-8")
    except Exception as e:
        logger.warning(f"Save profile: {e}")


# ═══════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════

def main():
    """Entry for `relay` command."""
    import sys as _sys
    import argparse

    p = argparse.ArgumentParser(description="RelayOS — Agent Workspace")
    p.add_argument("cmd", nargs="?", default="ui")
    p.add_argument("args", nargs="*")
    a = p.parse_args()

    # Piped input mode: echo "msg" | relay
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
            print(f"  {w['emoji']} {w['name']:<15} {w['role']:<14} {w['status']:<8} {w['provider']}")
    else:
        from relayos.cli.main import cli as cli_main
        _sys.argv = ["relay", a.cmd] + a.args
        cli_main()


if __name__ == "__main__":
    main()
