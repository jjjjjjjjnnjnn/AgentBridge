"""RelayOS Terminal UI — AI Control Panel.

Like htop for your AI team.
Switch profiles with one keypress.
See everything at a glance.
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
    import threading
    wm = WorkerManager()
    start_time = time.time()
    running = True
    current_profile = ["balanced"]  # mutable for key handler
    selected = [0]  # selected worker index

    def check_keys():
        nonlocal running
        getch = _getch if sys.platform != "win32" else _getch_win
        while running:
            try:
                key = getch()
                if key in ("q",): running = False
                elif key == "r": pass  # auto-refresh
                elif key == "f": _set_profile(current_profile, "free")
                elif key == "b": _set_profile(current_profile, "balanced")
                elif key == "q_": _set_profile(current_profile, "quality")
                elif key == "o": _set_profile(current_profile, "opencode")
                elif key == "m": _set_profile(current_profile, "mimo")
                elif key == "c": _set_profile(current_profile, "claude")
                elif key in "123456789":
                    idx = int(key) - 1
                    selected[0] = idx
            except: break

    kt = threading.Thread(target=check_keys, daemon=True)
    kt.start()

    with Live(refresh_per_second=4, screen=True) as live:
        try:
            while running:
                layout = _build_layout(wm, start_time, current_profile[0], selected[0])
                live.update(layout)
                live.refresh()
                time.sleep(1.5)
        except KeyboardInterrupt:
            pass
    print("\033[2J\033[H", end="")


def _set_profile(store: list, profile: str):
    store[0] = profile
    try:
        from relayos.config import get_config_dir
        import yaml
        p = get_config_dir() / "config.yaml"
        if p.exists():
            c = yaml.safe_load(p.read_text()) or {}
            c.setdefault("routing", {})["default"] = profile
            p.write_text(yaml.dump(c, default_flow_style=False), encoding="utf-8")
    except: pass


def _getch() -> str:
    import termios, tty, select
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        if select.select([sys.stdin], [], [], 0.1)[0]:
            return sys.stdin.read(1).lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ""


def _getch_win() -> str:
    import msvcrt
    if msvcrt.kbhit():
        return msvcrt.getch().decode(errors="ignore").lower()
    return ""


def _build_layout(wm: WorkerManager, start: float, profile: str, sel: int) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["header"].update(_render_header(wm, start, profile))
    layout["body"].update(_render_body(wm, sel))
    layout["footer"].update(_render_footer(wm, profile))
    return layout


def _render_header(wm: WorkerManager, start: float, profile: str) -> Panel:
    stats = wm.stats()
    elapsed = int(time.time() - start)
    t = Text()
    t.append(" RelayOS ", style="bold blue")
    t.append(f" Workers:{stats['total_workers']} ", style="cyan")
    t.append(f" Idle:{stats['idle']} ", style="green")
    t.append(f" Busy:{stats['busy']} ", style="yellow")
    t.append(f" Tasks:{stats['total_tasks']} ", style="white")
    t.append(f" [{elapsed}s] ", style="dim")
    t.append(f" Profile:{profile} ", style="bold cyan" if profile in ("free",) else "white")
    return Panel(t, style="blue")


def _render_body(wm: WorkerManager, sel: int) -> Layout:
    body = Layout()
    body.split_row(Layout(name="workers", ratio=3), Layout(name="panel", ratio=2))
    body["workers"].update(_render_workers(wm, sel))
    body["panel"].update(_render_panel(wm))
    return body


def _render_workers(wm: WorkerManager, sel: int) -> Panel:
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("#", width=2)
    table.add_column("Worker", width=14)
    table.add_column("Status", width=8)
    table.add_column("Model", width=28)
    table.add_column("Tasks", justify="right", width=5)

    team = wm.get_team()
    for i, w in enumerate(team):
        sel_style = "reverse" if i == sel else ""
        s = w["status"]
        ss = {"idle": "green", "busy": "yellow", "error": "red"}.get(s, "white")
        label = f"● {s}" if s == "busy" else f"○ {s}" if s == "idle" else s
        table.add_row(
            str(i + 1) if i == sel else " ",
            f"{w['emoji']} {w['name']}",
            Text(label, style=ss),
            f"{w['provider']}/{w['model'][:20]}",
            str(w["task_count"]),
            style=sel_style,
        )
    return Panel(table, title="[bold]Workers (1-9 select)[/bold]", border_style="dim")


def _render_panel(wm: WorkerManager) -> Layout:
    p = Layout()
    p.split_column(Layout(name="info", ratio=2), Layout(name="actions", ratio=1))
    p["info"].update(_render_info(wm))
    p["actions"].update(_render_actions())
    return p


def _render_info(wm: WorkerManager) -> Panel:
    from relayos.config import load_config
    import yaml
    lines = []
    # Routing info
    try:
        cfg = load_config()
        r = getattr(cfg, "routing", None)
        if r:
            lines.append(f"  Profile: {r.default}")
    except: pass
    lines.append("")
    # Cost
    try:
        from relayos.cost import CostManager
        r = CostManager().get_report()
        if r["total_cost"] > 0:
            lines.append(f"  Cost: ${r['total_cost']:.4f}")
        else:
            lines.append("  Cost: $0.00")
        for p, d in list(r.get("providers", {}).items())[:3]:
            lines.append(f"    {p}: ${d['cost']:.4f}")
    except: pass
    lines.append("")
    # Tasks
    try:
        from relayos.core.state import StateStore
        ss = StateStore()
        lines.append(f"  Pending: {ss.inbox_count()}")
    except: pass
    return Panel("\n".join(lines), title="[bold]Status[/bold]", border_style="dim")


def _render_actions() -> Panel:
    tips = Text()
    tips.append(" Profile: f=free b=balanced q=quality\n", style="bold cyan")
    tips.append(" Terminal: o=opencode m=mimo c=claude\n", style="dim")
    tips.append(" Commands:\n", style="bold cyan")
    tips.append("  1-9 select worker\n", style="dim")
    tips.append("  r refresh  q quit\n", style="dim")
    return Panel(tips, title="[bold]Actions[/bold]", border_style="dim")


def _render_footer(wm: WorkerManager, profile: str) -> Panel:
    stats = wm.stats()
    t = Text()
    t.append(f" {stats['total_workers']}w {stats['idle']}i {stats['busy']}b", style="green")
    t.append("  |  ", style="dim")

    try:
        from relayos.core.state import StateStore
        ic = StateStore().inbox_count()
        t.append(f"inbox:{ic}", style="yellow" if ic else "dim")
    except: t.append("inbox:-", style="dim")
    t.append("  |  ", style="dim")

    try:
        from relayos.cost import CostManager
        r = CostManager().get_report()
        t.append(f"${r['total_cost']:.4f}", style="white" if r['total_cost'] > 0 else "dim")
    except: t.append("$0", style="dim")
    t.append("  |  ", style="dim")

    t.append(f"[{profile}]", style="cyan")
    t.append("  |  q=quit 1-9=select f/b/q/o/m/c=switch", style="dim")
    return Panel(t, style="green", height=3)


def main():
    import argparse
    p = argparse.ArgumentParser(description="RelayOS — AI Control Panel")
    p.add_argument("cmd", nargs="?", default="ui")
    p.add_argument("args", nargs="*")
    a = p.parse_args()

    if a.cmd in ("ui", "tui", ""):
        run_tui()
    elif a.cmd == "workers":
        wm = WorkerManager()
        for w in wm.get_team():
            print(f"{w['emoji']} {w['name']:<15} {w['role']:<14} {w['status']:<8} {w['provider']}")
    else:
        from relayos.cli.main import cli as cli_main
        import sys as _sys
        _sys.argv = ["relay", a.cmd] + a.args
        cli_main()


if __name__ == "__main__":
    main()
