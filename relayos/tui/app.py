"""RelayOS TUI — Conversation Graph Workspace.

Layout: Status bar | Messages | Input

Core differentiators:
  - Conversation Graph (fork/merge/attach)
  - Cross-session Knowledge
  - AUTO mode: workers auto-assigned

Ctrl+P = command palette (ALL settings)
"""
from __future__ import annotations

import logging
import sys
import time
import uuid
from pathlib import Path

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)

CTRL_P = "\x10"; CTRL_C = "\x03"
CTRL_U = "\x15"; CTRL_A = "\x01"; CTRL_E = "\x05"
TAB = "\x09"; TAB_BACK = "^Z"; ESC = "\x1b"; ENTER = "\r"
BS = "\x7f"    # DEL (Unix raw mode)
BS_WIN = "\x08"  # Backspace (Windows)


def _getch() -> str:
    if sys.platform == "win32":
        import msvcrt, ctypes
        try:
            if not msvcrt.kbhit(): return ""
            cp = ctypes.windll.kernel32.GetConsoleCP()
            raw = msvcrt.getch()

            # Extended keys: \xe0 (arrow/function) and \x00 (special)
            if raw in (b'\xe0', b'\x00'):
                key = msvcrt.getch()
                if key == b'H': return "^A"  # Up
                if key == b'P': return "^B"  # Down
                if key == b'K': return "^D"  # Left
                if key == b'M': return "^C"  # Right
                return ""

            # ANSI escape sequences (\x1b[A etc.) — used by Windows Terminal
            if raw == b'\x1b':
                # First follower bytes should arrive within 5ms of the leader
                nxt = b''
                for _ in range(5):
                    if msvcrt.kbhit():
                        nxt = msvcrt.getch()
                        break
                    time.sleep(0.001)
                if nxt == b'[':
                    nxt2 = b''
                    for _ in range(5):
                        if msvcrt.kbhit():
                            nxt2 = msvcrt.getch()
                            break
                        time.sleep(0.001)
                    if nxt2 == b'A': return "^A"  # Up
                    if nxt2 == b'B': return "^B"  # Down
                    if nxt2 == b'D': return "^D"  # Left
                    if nxt2 == b'C': return "^C"  # Right
                    if nxt2 == b'Z': return "^Z"  # Shift+Tab
                return ""  # Discard partial sequences

            return raw.decode(f'cp{cp}')
        except Exception: return ""
    else:
        import termios, tty, select
        try:
            fd = sys.stdin.fileno(); old = termios.tcgetattr(fd)
            tty.setraw(fd)
            try:
                if select.select([sys.stdin], [], [], 0.03)[0]:
                    ch = sys.stdin.read(1)
                    if ch == ESC:
                        if select.select([sys.stdin], [], [], 0.01)[0]:
                            r = sys.stdin.read(1)
                            if r == "[" and select.select([sys.stdin], [], [], 0.01)[0]:
                                r += sys.stdin.read(1)
                            if r.startswith("["): return f"^{r[1:]}"
                        return ESC
                    return ch
            finally: termios.tcsetattr(fd, termios.TCSADRAIN, old)
        except Exception: return ""


# ── Command Tree ───────────────────────────────────────────────
COMMANDS = [
    {"cat": "Session", "items": [
        {"name": "New Session", "desc": "Start fresh conversation", "action": "new_session"},
        {"name": "Fork Session", "desc": "Branch from current session", "action": "fork_session"},
        {"name": "Merge Sessions", "desc": "Combine multiple sessions", "action": "merge_session"},
        {"name": "Switch Session", "desc": "Browse all sessions", "action": "switch_session"},
        {"name": "Attach Session", "desc": "Import context from another session", "action": "attach_session"},
    ]},
    {"cat": "Knowledge", "items": [
        {"name": "Remember Fact", "desc": "Save knowledge: /remember key: value", "action": "remember_fact"},
        {"name": "Browse Knowledge", "desc": "Explore stored facts", "action": "knowledge_view"},
    ]},
    {"cat": "Settings", "items": [
        {"name": "Toggle Mode", "desc": "Auto / Edit", "action": "toggle_mode"},
        {"name": "Budget", "desc": "Spending limits", "action": "cost_report"},
        {"name": "Help", "desc": "Keyboard shortcuts", "action": "show_help"},
    ]},
    {"cat": "System", "items": [
        {"name": "Quit", "desc": "Exit RelayOS", "action": "quit"},
    ]},
]

_ALL_ITEMS = []
for cat in COMMANDS:
    for item in cat["items"]:
        item["cat"] = cat["cat"]
        _ALL_ITEMS.append(item)


def run_tui():
    from relayos.core.session import SessionStore
    from relayos.core.budget import BudgetGuard
    ss = SessionStore(); bg = BudgetGuard()
    start = time.time()

    buf = []; msgs = []; history = []; hi = -1
    sess = None  # current Session
    view = "chat"  # chat | palette | sessions | graph
    pal_filter = ""; pal_sel = 0
    session_search = ""; session_focus = "search"; session_items = []
    mode_state = "auto"  # auto | edit | group
    tab_provider_idx = 0
    tab_providers = []
    # Load CLI providers
    try:
        from relayos.providers import detect_providers
        _all = detect_providers()
        tab_providers = [p for p in _all if p.type == "cli" and p.enabled]
    except Exception:
        tab_providers = []

    layout = Layout()
    layout.split_column(Layout(name="header", size=1),
                        Layout(name="body", ratio=1),
                        Layout(name="footer", size=3))

    def add(role, src, text):
        msgs.append({"role": role, "from": src, "content": text})

    def session_label(s=None) -> str:
        s = s or sess; return s.id[:10] if s else "—"

    def parent_hint(s=None) -> str:
        s = s or sess
        if not s: return ""
        try:
            parents = ss.get_conversation_parents(s.id)
            if parents:
                tags = [f"#{p[:6]}" for p in parents[:3]]
                return "Derived: " + ", ".join(tags)
        except Exception: pass
        return ""

    def budget_str() -> str:
        try:
            s = bg.get_status()
            return f"${s['today']:.3f}" if s['today'] > 0 else "$0"
        except Exception: return "$0"

    def submit():
        nonlocal hi, sess
        text = "".join(buf).strip()
        if not text: return
        history.append(text); hi = -1; buf.clear()

        # ── Slash commands ──
        if text.startswith("/"):
            parts = text[1:].split()
            cmd = parts[0].lower()

            if cmd == "new":
                s = ss.create_session(f"Conv-{uuid.uuid4().hex[:6]}")
                sess = s; msgs.clear()
                add("sys", "", f"New session: {s.id}")

            elif cmd == "fork":
                if not sess:
                    add("sys", "", "No session to fork. Start a conversation first.")
                    return
                pid = sess.id
                child = ss.fork_session(pid)
                sess = child; msgs.clear()
                m = ss.get_messages(child.id, 30)
                for x in m:
                    d = x.to_dict()
                    msgs.append({"role": d.get("role",""), "from": d.get("from",""), "content": d.get("content","")})
                add("sys", "", f"Forked -> {child.id[:10]} (from {pid[:10]})")

            elif cmd == "merge":
                if len(parts) < 2:
                    add("sys", "", "Usage: /merge <session_id1> [session_id2 ...]")
                    return
                ids = [p for p in parts[1:]]
                child = ss.merge_sessions(ids)
                sess = child; msgs.clear()
                for pid in ids:
                    mx = ss.get_messages(pid, 50)
                    for x in mx:
                        d = x.to_dict()
                        msgs.append({"role": d.get("role",""), "from": d.get("from",""), "content": d.get("content","")})
                add("sys", "", f"Merged {len(ids)} sessions → {child.id[:10]}")

            elif cmd == "attach":
                if len(parts) < 2:
                    add("sys", "", "Usage: /attach <session_id>")
                    return
                pid = parts[1]
                mx = ss.get_messages(pid, 30)
                add("sys", "", f"Attached {len(mx)} messages from {pid[:10]} (use /merge to combine)")

            elif cmd == "remember":
                rest = " ".join(parts[1:])
                if ":" not in rest:
                    add("sys", "", "Usage: /remember key: value")
                    return
                key, _, val = rest.partition(":")
                key = key.strip(); val = val.strip()
                try:
                    from relayos.core.knowledge import ProjectStore
                    ps = ProjectStore()
                    pid = sess.project_id if sess else ""
                    if not pid:
                        pid = ps.create_project("default")
                        if sess:
                            ss._conn.execute("UPDATE sessions SET project_id=? WHERE id=?", (pid, sess.id))
                            ss._conn.commit()
                    ps.upsert_knowledge(pid, "general", key, val)
                    add("sys", "", f"Remembered: {key} = {val}")
                except Exception as e:
                    add("sys", "", f"Failed to save: {e}")

            elif cmd == "clear":
                msgs.clear()

            elif cmd == "help":
                msgs.clear()
                add("sys", "", "RelayOS — Conversation Graph Workspace")
                add("sys", "", "")
                add("sys", "", " Unique features:")
                add("sys", "", "  /fork         Branch current session")
                add("sys", "", "  /merge <ids>  Merge sessions together")
                add("sys", "", "  /attach <id>  Import session context")
                add("sys", "", "  /remember k:v Save knowledge")
                add("sys", "", "")
                add("sys", "", " Basic:")
                add("sys", "", "  /new          New session")
                add("sys", "", "  /clear        Clear messages")
                add("sys", "", "  /cost         Spending report")
                add("sys", "", "  /mode         Toggle auto/edit")
                add("sys", "", "")
                add("sys", "", " Shortcuts:")
                add("sys", "", "  Ctrl+P        Command palette (all settings)")
                add("sys", "", "  Esc           Cancel / clear input")
                add("sys", "", "  Esc           Cancel")
                add("sys", "", "  Up/Dn         History")

            elif cmd == "cost":
                s = bg.get_status()
                add("sys", "", f"Today: ${s['today']:.4f} / ${s['daily_limit']:.2f}")

            elif cmd == "mode":
                modes = ["auto", "edit", "group"]
                mode_state = modes[(modes.index(mode_state) + 1) % len(modes)]
                add("sys", "", f"Mode: {mode_state}")
            else:
                add("sys", "", f"Unknown: /{cmd}. Try /help")
            return

        # ── Regular chat ──
        add("user", "you", text)
        from relayos.providers import create_provider
        try:
            # Use selected CLI provider, or first enabled, or fallback to API engine
            provider = None
            if tab_providers and 0 <= tab_provider_idx < len(tab_providers):
                provider = create_provider(tab_providers[tab_provider_idx])
            if not provider:
                _avail = [create_provider(p) for p in detect_providers() if p.enabled]
                if _avail:
                    provider = _avail[0]
            if provider:
                result = provider.complete(text)
                content = result.content[:500] if result.content else ""
                model_name = result.model or provider.config.display_name
                add("assistant", model_name, content)
                # Auto-create session
                if not sess:
                    sess = ss.create_session(f"Conv-{uuid.uuid4().hex[:6]}")
                ss.add_message(sess.id, "user", "user", text)
                ss.add_message(sess.id, "assistant", model_name, content)
            else:
                add("sys", "", f"[ERR] No CLI provider available. Install mimo, claude, or opencode.")
        except Exception as e:
            add("sys", "", f"[ERR] {e}")

    def execute_action(action: str):
        nonlocal sess, view, sl_sel, mode_state, buf
        if action == "new_session":
            s = ss.create_session(f"Conv-{uuid.uuid4().hex[:6]}")
            sess = s; msgs.clear()
            add("sys", "", f"New: {s.id}")
        elif action == "switch_session":
            nonlocal sessions_list
            session_search = ""; session_focus = "search"; sl_sel = 0
            sessions_list = ss.search_sessions(); session_items = list(sessions_list)
            view = "sessions"
        elif action == "toggle_mode":
            modes = ["auto", "edit", "group"]
            mode_state = modes[(modes.index(mode_state) + 1) % len(modes)]
            add("sys", "", f"Mode: {mode_state}")
        elif action == "fork_session":
            if sess:
                pid = sess.id
                child = ss.fork_session(pid)
                sess = child; msgs.clear()
                mx = ss.get_messages(child.id, 50)
                for x in mx:
                    msgs.append({"role": x.role, "from": x.from_worker, "content": x.content})
                add("sys", "", f"Forked -> {child.id[:10]} (from {pid[:10]})")
            else:
                add("sys", "", "No session to fork. Start a conversation first.")
        elif action == "merge_session":
            add("sys", "", "Usage: /merge <session_id1> [session_id2 ...]")
        elif action == "attach_session":
            add("sys", "", "Usage: /attach <session_id>")
        elif action == "remember_fact":
            add("sys", "", "Usage: /remember key: value")
        elif action == "cost_report":
            s = bg.get_status()
            add("sys", "", f"Today: ${s['today']:.4f} / ${s['daily_limit']:.2f}")
        elif action == "show_help":
            old = list(buf); buf.clear()
            for ch in "/help": buf.append(ch)
            submit()
            buf = old
        elif action == "knowledge_view":
            try:
                from relayos.core.knowledge import ProjectStore
                ps = ProjectStore()
                projects = ps.list_projects()
                if projects:
                    add("sys", "", f"Projects: {len(projects)}")
                    for p in projects[:5]:
                        k = ps.query_knowledge(p["id"], max_items=3)
                        add("sys", "", f"  {p['name']}: {len(k)} facts")
                        for item in k[:3]:
                            add("sys", "", f"    {item['key']} = {item.get('value','')[:50]}")
                else:
                    add("sys", "", "No knowledge stored. Use /remember key: value")
            except Exception as e:
                add("sys", "", f"Knowledge: {e}")
        elif action == "quit":
            sys.exit(0)

    # Build palette items
    def pal_items(filter_str=""):
        if not filter_str: return list(_ALL_ITEMS)
        f = filter_str.lower()
        return [it for it in _ALL_ITEMS if f in it["name"].lower() or f in it["cat"].lower() or f in it.get("desc","").lower()]

    # Main loop
    sessions_list = []; sl_sel = 0
    with Live(layout, refresh_per_second=8, screen=True) as live:
        try:
            while True:
                key = _getch()

                # ── Palette ──
                if view == "palette":
                    if key in (ESC, CTRL_P): view = "chat"; pal_filter = ""; pal_sel = 0
                    elif key == ENTER:
                        items = pal_items(pal_filter)
                        if 0 <= pal_sel < len(items):
                            execute_action(items[pal_sel].get("action",""))
                        view = "chat"; pal_filter = ""; pal_sel = 0
                    elif key in (BS, BS_WIN): pal_filter = pal_filter[:-1]; pal_sel = 0
                    elif key == "^A": pal_sel = max(0, pal_sel - 1)
                    elif key == "^B": pal_sel = min(len(pal_items(pal_filter))-1, pal_sel + 1)
                    elif key and len(key)==1 and key.isprintable(): pal_filter += key; pal_sel = 0

                # ── Sessions ──
                elif view == "sessions":
                    if key == ESC:
                        session_search = ""; view = "chat"
                    elif key == TAB:
                        session_focus = "list" if session_focus == "search" else "search"
                    elif key == "^A":  # Up
                        if session_focus == "list" and session_items:
                            sl_sel = max(0, sl_sel - 1)
                        elif session_focus == "search" and session_items:
                            session_focus = "list"; sl_sel = len(session_items) - 1
                    elif key == "^B":  # Down
                        if session_focus == "list" and session_items:
                            sl_sel = min(len(session_items)-1, sl_sel + 1)
                        elif session_focus == "search" and session_items:
                            session_focus = "list"; sl_sel = 0
                    elif key == "^D":  # Left — switch to search
                        session_focus = "search"
                    elif key == "^C":  # Right — switch to list
                        if session_items: session_focus = "list"
                    elif key == ENTER and session_items:
                        idx = sl_sel
                        if 0 <= idx < len(session_items):
                            s = ss.get_session(session_items[idx]["id"])
                            if s: sess = s; msgs.clear()
                            mx = ss.get_messages(s.id, 30) if s else []
                            for x in mx:
                                d = x.to_dict()
                                msgs.append({"role":d.get("role",""), "from":d.get("from",""), "content":d.get("content","")})
                            view = "chat"; session_search = ""
                    elif key == "d" and session_items:
                        idx = sl_sel
                        if 0 <= idx < len(session_items):
                            ss.delete_session(session_items[idx]["id"])
                            sessions_list = ss.search_sessions(session_search); session_items = list(sessions_list)
                            sl_sel = min(sl_sel, len(session_items)-1)
                    elif key in (BS, BS_WIN):  # Backspace in search
                        if session_search:
                            session_search = session_search[:-1]
                            sessions_list = ss.search_sessions(session_search); session_items = list(sessions_list)
                            sl_sel = 0
                    elif key and len(key) == 1 and key.isprintable():  # Type to search
                        session_search += key
                        sessions_list = ss.search_sessions(session_search); session_items = list(sessions_list)
                        sl_sel = 0
                        session_focus = "list" if session_items else "search"

                # ── Graph ──
                elif view == "graph":
                    if key == ESC: view = "chat"

                # ── Chat ──
                if view == "chat":
                    if key == CTRL_P: view = "palette"; pal_filter = ""; pal_sel = 0
                    elif key == ENTER: submit()
                    elif key == TAB:
                        if tab_providers:
                            tab_provider_idx = (tab_provider_idx + 1) % len(tab_providers)
                            add("sys", "", f"Provider: {tab_providers[tab_provider_idx].display_name}")
                    elif key == TAB_BACK:
                        modes = ["auto", "edit", "group"]
                        mode_state = modes[(modes.index(mode_state) + 1) % len(modes)]
                        add("sys", "", f"Mode: {mode_state}")
                    elif key == ESC:
                        if buf: buf.clear()
                    elif key in (BS, BS_WIN):
                        if buf: buf.pop()
                    elif key == CTRL_C: break
                    elif key == CTRL_U: buf.clear()
                    elif key == "^A":
                        if history:
                            hi = len(history) - 1 if hi <= -1 else max(0, hi - 1)
                            buf = list(history[hi]) if 0 <= hi < len(history) else []
                    elif key == "^B":
                        if history and hi >= 0:
                            hi += 1
                            if hi < len(history):
                                buf = list(history[hi])
                            else:
                                hi = -1
                                buf = []
                    elif key and len(key)==1: buf.append(key)

                # ── Render ──
                ph = parent_hint()
                bc = budget_str()
                sl = session_label()

                # Status bar — show graph info prominently
                h_parts = [(" RelayOS ", "bold blue"), (f" {sl} ", "cyan")]
                if ph:
                    h_parts.append((f" {ph} ", "yellow"))
                # Show current provider
                tp_name = ""
                if tab_providers and 0 <= tab_provider_idx < len(tab_providers):
                    tp_name = tab_providers[tab_provider_idx].display_name[:10]
                if tp_name:
                    h_parts.append((f" [{tp_name}]", "cyan"))
                h_parts.append((f" [{mode_state.upper()}]", "green"))
                h_parts.append((f" {bc}", "dim"))
                layout["header"].update(Panel(Text.assemble(*h_parts), style="bold", height=1))

                # Body
                lines = []
                if view == "palette":
                    items = pal_items(pal_filter)
                    lines.append("  Command Palette  (Esc close)")
                    lines.append("  " + "-"*55)
                    shown = []
                    for i, it in enumerate(items):
                        if it["cat"] not in shown:
                            shown.append(it["cat"]); lines.append(f"  {it['cat']}:")
                        sel = " >" if i == pal_sel else "  "
                        lines.append(f"{sel} {it['name']:<25} {it.get('desc','')}")
                    lines.append(f"  Filter: {pal_filter or '(type to filter)'}")
                    lines.append("  Up/Down | Enter | Esc")

                elif view == "graph":
                    if key == ESC:
                        view = "chat"
                    lines.append("  Conversation Graph  (Esc back, Tab cycle)")
                    lines.append("  " + "-"*55)
                    graph_text = ss.build_graph_ascii(sess.id if sess else "")
                    for line in graph_text.split("\n"):
                        lines.append(f"  {line}")
                    lines.append("")
                    lines.append("  > current session")
                    lines.append("  Esc to close")

                elif view == "sessions":
                    lines.append("  Sessions  (Esc to close)")
                    lines.append("  " + "-"*55)
                    # Search bar
                    search_disp = session_search if session_search else "type to search"
                    sf = " >" if session_focus == "search" else "  "
                    cur = "|" if session_focus == "search" else ""
                    lines.append(f"{sf} Search: {search_disp}{cur}")
                    lines.append("")
                    # Session list
                    items = session_items if session_items else sessions_list
                    if not items:
                        lines.append("  No sessions found. Start a new conversation!")
                    else:
                        for i, s in enumerate(items):
                            sel = " >" if i == sl_sel and session_focus == "list" else "  "
                            name = s.get("name","?")[:28]
                            ts = s.get("updated_at",0)
                            ago = f"{int((time.time()-ts)/60)}m" if ts else ""
                            model = s.get("last_model","")[:12]
                            preview = s.get("preview","")[:50]
                            # Parent hint
                            par = ""
                            try:
                                pids = ss.get_conversation_parents(s["id"])
                                if pids: par = f" [#{len(pids)}]"
                            except Exception:
                                pass
                            pmodel = f" [{model}]" if model else ""
                            pp = f"  {preview}" if preview else ""
                            lines.append(f"{sel} {name:<28}{pmodel:<14}{ago:>8}{par}")
                            if preview:
                                lines.append(f"     {pp}")
                    lines.append("")
                    lines.append("  Tab=switch  ↑↓=navigate  Enter=open  d=delete  Esc=close")

                else:
                    if not msgs:
                        lines.append("")
                        lines.append("  RelayOS — Conversation Graph Workspace")
                        lines.append("  " + "-"*50)
                        lines.append("  Type a task below, press Enter.")
                        lines.append("  /fork  /merge  /attach  /remember  /help")
                        lines.append("  Ctrl+P for command palette")
                        lines.append("")

                    for m in msgs[-40:]:
                        r = m.get("role",""); f = m.get("from",""); c = m.get("content","")
                        if r == "sys":
                            for line in c.split("\n"): lines.append(f"  {line}")
                        elif r == "user":
                            for line in c.split("\n")[:2]: lines.append(f"  > {line}")
                        else:
                            for line in c.split("\n")[:8]:
                                if len(lines) > 200: break
                                lines.append(f"  [{f}] {line}")

                layout["body"].update(Panel("\n".join(lines[-80:]), border_style="dim"))

                # Footer
                inp = "".join(buf)
                foot = [f"> {inp}" + ("█" if view == "chat" else "")]
                if view == "chat":
                    foot.append("  Ctrl+P=palette  /fork  /merge  /remember  /help  Tab=provider")
                layout["footer"].update(Panel("\n".join(foot), style="green", height=3))

                live.refresh()
                time.sleep(0.03)

        except KeyboardInterrupt: pass

    print("\033[2J\033[H", end="")


def get_config_dir() -> Path:
    from relayos.config import get_config_dir as _g; return _g()


def auto_dispatch(task: str) -> dict:
    from relayos.core.conversation import ConversationEngine
    return ConversationEngine().chat(task)


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("cmd", nargs="?")
    p.add_argument("args", nargs="*")
    a = p.parse_args()
    if a.cmd and a.cmd not in ("ui","tui",""):
        task = a.cmd + " " + " ".join(a.args)
        try:
            r = auto_dispatch(task)
            print(r.get("content",""))
        except Exception as e: print(f"[ERR] {e}", file=sys.stderr)
        return
    run_tui()


if __name__ == "__main__":
    main()
