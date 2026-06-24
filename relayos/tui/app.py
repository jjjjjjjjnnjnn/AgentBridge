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
from pathlib import Path

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)

CTRL_P = "\x10"; CTRL_X = "\x18"; CTRL_C = "\x03"
TAB = "\x09"; ESC = "\x1b"; ENTER = "\r"; BS = "\x7f"


def _getch() -> str:
    if sys.platform == "win32":
        import msvcrt, ctypes
        try:
            if not msvcrt.kbhit(): return ""
            cp = ctypes.windll.kernel32.GetConsoleCP()
            raw = msvcrt.getch()
            if raw in (b'\xe0', b'\x00'): msvcrt.getch(); return ""
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
        except: return ""


# ── Command Tree ───────────────────────────────────────────────
COMMANDS = [
    {"cat": "Session", "items": [
        {"name": "New Session", "key": "Ctrl+X N", "desc": "Start fresh conversation", "action": "new_session"},
        {"name": "Fork Session", "key": "/fork", "desc": "Branch from current session", "action": "fork_session"},
        {"name": "Merge Sessions", "key": "/merge", "desc": "Combine multiple sessions", "action": "merge_session"},
        {"name": "Switch Session", "key": "Ctrl+X S", "desc": "Browse all sessions", "action": "switch_session"},
        {"name": "Attach Session", "key": "/attach", "desc": "Import context from another session", "action": "attach_session"},
    ]},
    {"cat": "Knowledge", "items": [
        {"name": "Remember Fact", "key": "/remember", "desc": "Save knowledge: /remember key: value", "action": "remember_fact"},
        {"name": "Browse Knowledge", "key": "Ctrl+X K", "desc": "Explore stored facts", "action": "knowledge_view"},
    ]},
    {"cat": "Settings", "items": [
        {"name": "Toggle Mode", "key": "Ctrl+X M", "desc": "Auto / Edit", "action": "toggle_mode"},
        {"name": "Budget", "key": "Ctrl+X C", "desc": "Spending limits", "action": "cost_report"},
        {"name": "Help", "key": "Ctrl+X ?", "desc": "Keyboard shortcuts", "action": "show_help"},
    ]},
    {"cat": "System", "items": [
        {"name": "Quit", "key": "Ctrl+C", "desc": "Exit RelayOS", "action": "quit"},
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
    start = time.time(); import uuid

    buf = []; msgs = []; history = []; hi = -1
    sess = None  # current Session
    view = "chat"  # chat | palette | sessions | graph
    pal_filter = ""; pal_sel = 0

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
        except: pass
        return ""

    def budget_str() -> str:
        try:
            s = bg.get_status()
            return f"${s['today']:.3f}" if s['today'] > 0 else "$0"
        except: return "$0"

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
                child = ss.fork_session(sess.id)
                sess = child; msgs.clear()
                m = ss.get_messages(child.id, 30)
                for x in m:
                    d = x.to_dict()
                    msgs.append({"role": d.get("role",""), "from": d.get("from",""), "content": d.get("content","")})
                add("sys", "", f"Forked → {child.id[:10]} (from {sess.id[:10] if sess else '?'})")

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
                count = 0
                for x in mx:
                    d = x.to_dict()
                    msgs.append({"role": d.get("role",""), "from": d.get("from",""), "content": d.get("content","")})
                    count += 1
                add("sys", "", f"Attached {count} messages from {pid[:10]}")

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
                add("sys", "", "  Ctrl+P        Command palette")
                add("sys", "", "  Ctrl+X N/S/M  New/Session/Mode")
                add("sys", "", "  Ctrl+X C/?    Cost/Help")
                add("sys", "", "  Tab           Switch provider")
                add("sys", "", "  Esc           Cancel")
                add("sys", "", "  Up/Dn         History")

            elif cmd == "cost":
                s = bg.get_status()
                add("sys", "", f"Today: ${s['today']:.4f} / ${s['daily_limit']:.2f}")

            elif cmd == "mode":
                from relayos.providers.router import ProviderRouter
                r = ProviderRouter()
                r.mode = "edit" if r.mode == "auto" else "auto"
                add("sys", "", f"Mode: {r.mode}")
            else:
                add("sys", "", f"Unknown: /{cmd}. Try /help")
            return

        # ── Regular chat ──
        add("user", "you", text)
        try:
            from relayos.core.conversation import ConversationEngine
            eng = ConversationEngine()
            r = eng.chat(text)
            add("assistant", r.get("worker","ai"), r.get("content","")[:500])
            # Auto-save to session
            sid = r.get("session_id","")
            if sid and not sess:
                sess = ss.get_session(sid)
        except Exception as e:
            add("sys", "", f"[ERR] {e}")

    def execute_action(action: str):
        nonlocal sess, view
        if action == "new_session":
            s = ss.create_session(f"Conv-{uuid.uuid4().hex[:6]}")
            sess = s; msgs.clear()
            add("sys", "", f"New: {s.id}")
        elif action == "switch_session":
            nonlocal sessions_list
            sessions_list = ss.list_sessions(20); sl_sel = 0
            view = "sessions"
        elif action == "toggle_mode":
            from relayos.providers.router import ProviderRouter
            r = ProviderRouter()
            r.mode = "edit" if r.mode == "auto" else "auto"
            add("sys", "", f"Mode: {r.mode}")
        elif action == "cost_report":
            s = bg.get_status()
            add("sys", "", f"Today: ${s['today']:.4f} / ${s['daily_limit']:.2f}")
        elif action == "show_help":
            submit.__globals__["_exec_help"] = True
            # Trigger help by simulating /help
            nonlocal buf
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
                    elif key == BS: pal_filter = pal_filter[:-1]; pal_sel = 0
                    elif key == "^A": pal_sel = max(0, pal_sel - 1)
                    elif key == "^B": pal_sel = min(len(pal_items(pal_filter))-1, pal_sel + 1)
                    elif key and len(key)==1 and key.isprintable(): pal_filter += key; pal_sel = 0
                    continue

                # ── Sessions ──
                if view == "sessions":
                    if key == ESC: view = "chat"
                    elif key == ENTER and sessions_list:
                        idx = sl_sel
                        if 0 <= idx < len(sessions_list):
                            s = ss.get_session(sessions_list[idx]["id"])
                            if s: sess = s; msgs.clear()
                            mx = ss.get_messages(s.id, 30) if s else []
                            for x in mx:
                                d = x.to_dict()
                                msgs.append({"role":d.get("role",""), "from":d.get("from",""), "content":d.get("content","")})
                            view = "chat"
                    elif key == "^A": sl_sel = max(0, sl_sel - 1)
                    elif key == "^B": sl_sel = min(len(sessions_list)-1, sl_sel + 1)
                    elif key == "d" and sessions_list:
                        idx = sl_sel
                        if 0 <= idx < len(sessions_list):
                            ss.delete_session(sessions_list[idx]["id"])
                            sessions_list = ss.list_sessions(20)
                            sl_sel = min(sl_sel, len(sessions_list)-1)
                    continue

                # ── Chat ──
                if key == CTRL_P: view = "palette"; pal_filter = ""; pal_sel = 0
                elif key == ENTER: submit()
                elif key == ESC:
                    if buf: buf.clear()
                elif key == BS:
                    if buf: buf.pop()
                elif key == CTRL_X:
                    time.sleep(0.1); nk = _getch()
                    if nk == "n":
                        s = ss.create_session(f"Conv-{uuid.uuid4().hex[:6]}")
                        sess = s; msgs.clear()
                        add("sys", "", f"New: {s.id}")
                    elif nk == "s":
                        sessions_list = ss.list_sessions(20); sl_sel = 0; view = "sessions"
                    elif nk == "m":
                        from relayos.providers.router import ProviderRouter
                        r = ProviderRouter(); r.mode = "edit" if r.mode == "auto" else "auto"
                        add("sys", "", f"Mode: {r.mode}")
                    elif nk == "c":
                        s = bg.get_status()
                        add("sys", "", f"Today: ${s['today']:.4f} / ${s['daily_limit']:.2f}")
                    elif nk == "k":
                        execute_action("knowledge_view")
                    elif nk == "g":
                        view = "graph"
                    elif nk == "?":
                        submit.__globals__["_tmp"] = list(buf); buf.clear()
                        for ch in "/help": buf.append(ch); submit()
                elif key == CTRL_C: break
                elif key == CTRL_U: buf.clear()
                elif key == "^A":
                    if history:
                        hi = max(-1, hi-1)
                        buf = list(history[min(hi,len(history)-1)]) if hi >= 0 else []
                elif key == "^B":
                    if history:
                        hi = min(len(history), hi+1)
                        buf = list(history[hi]) if 0 <= hi < len(history) else []
                elif key and len(key)==1: buf.append(key)

                # ── Render ──
                ph = parent_hint()
                bc = budget_str()
                sl = session_label()

                # Status bar — show graph info prominently
                h_parts = [(" RelayOS ", "bold blue"), (f" {sl} ", "cyan")]
                if ph:
                    h_parts.append((f" {ph} ", "yellow"))
                h_parts.append((" [AUTO]", "green"))
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
                        k = f" ({it['key']})" if it.get("key") else ""
                        lines.append(f"{sel} {it['name']:<25}{k:<15}{it.get('desc','')}")
                    lines.append(f"  Filter: {pal_filter or '(type)'}")
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
                    lines.append("  Ctrl+X G to refresh | Esc to close")

                elif view == "sessions":
                    lines.append("  Sessions  (Esc back, d delete)")
                    lines.append("  " + "-"*55)
                    for i, s in enumerate(sessions_list):
                        sel = " >" if i == sl_sel else "  "
                        name = s.get("name","?")[:30]
                        ts = s.get("updated_at",0)
                        ago = f"{int((time.time()-ts)/60)}m ago" if ts else ""
                        par = ""
                        try:
                            pids = ss.get_conversation_parents(s["id"])
                            if pids: par = f" <- {len(pids)} merged"
                        except: pass
                        lines.append(f"{sel} {name:<30} {ago:<10}{par}")
                    lines.append("")
                    lines.append("  Enter=open  d=delete  Esc=back")

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
                    foot.append("  Ctrl+P=palette  /fork  /merge  /remember  /help")
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
