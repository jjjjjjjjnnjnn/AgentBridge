<p align="center">
  <strong>Git for AI Conversations.</strong><br>
  Fork, merge, and weave AI conversations together.
</p>

<p align="center">
  <video src="docs/demo.mp4" controls width="800" autoplay loop muted>
    Your browser does not support the video tag. <a href="docs/demo.mp4">Download video</a>
  </video>
</p>

<p align="center">
  <code>pip install relayos && relay</code>
</p>

<p align="center">
  <a href="https://github.com/jjjjjjjjnnjnn/relayos"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github" alt="GitHub"></a>
  <a href="#-quick-start"><img src="https://img.shields.io/badge/Quick_Start-10B981?style=for-the-badge" alt="Quick Start"></a>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文-EA4335?style=flat-square" alt="中文"></a>
  <a href="README_DE.md"><img src="https://img.shields.io/badge/Deutsch-FFD700?style=flat-square" alt="Deutsch"></a>
  <a href="README_ES.md"><img src="https://img.shields.io/badge/Español-00C853?style=flat-square" alt="Español"></a>
  <a href="README_FR.md"><img src="https://img.shields.io/badge/Français-1E90FF?style=flat-square" alt="Français"></a>
  <a href="README_JP.md"><img src="https://img.shields.io/badge/日本語-FF4081?style=flat-square" alt="日本語"></a>
  <a href="README_KR.md"><img src="https://img.shields.io/badge/한국어-03C75A?style=flat-square" alt="한국어"></a>
</p>

---

## 👋 The Problem

You switch between ChatGPT, Claude, Gemini, and DeepSeek. You copy output from one, paste into the next. You lose context between sessions. **You spend 30% of your time managing tools instead of building.**

And when you have a conversation that matters — a system design, an architecture review — it's trapped in a single session. You can't branch it, merge it, or build on it later.

## 🎯 The Solution

**RelayOS treats AI conversations like code.** Fork, merge, and weave them together.

```
#12 数据库设计                          #25 API设计
       │                                    │
       ├── /fork → #18 数据库v2              │
       │                                    │
       └────────── /merge ──────────────────┘
                            │
                            ▼
                         #31 系统架构
                         (Derived: #12 #25)
```

**Zero config.** Auto-detects your installed AI CLIs.

```
pip install relayos && relay
```

---

## ✨ What Makes RelayOS Different

| Feature | What It Does |
|---------|-------------|
| 🔀 **Conversation Graph** | `/fork` `/merge` `/attach` — Git for conversations |
| 🧠 **Auto Routing** | CLI-first, zero-config, auto-detects installed tools |
| 💰 **Budget Guard** | Per-task/daily/monthly hard limits, no surprise bills |
| 🔌 **Unified Provider** | API + CLI — zero-config, Tab to cycle providers |
| ⌨️ **OpenCode-Style TUI** | Ctrl+P command palette, Tab/Shift+Tab, Switch Session panel |
| 💾 **Cross-Session Memory** | `/remember` facts that persist across conversations |
| 🌐 **i18n** | Chinese + English auto-detect |
| 🚀 **3 Modes** | Auto (no ask) / Edit (confirm) / Group (multi-provider) |

---

## ⚡ Quick Start

```bash
pip install relayos
relay
```

Opens the workspace. Type a task, press Enter.

**No config required.** RelayOS auto-detects your installed AI CLIs (claude, opencode, mimo, etc.) If none found, the setup wizard guides you.

### One-liner tasks

```bash
relay "设计一个支付系统"        # Auto-routes to best workers
relay "Review this code"        # Detects intent automatically
relay "Explain Kubernetes"      # Single chat
```

### Conversation branching

```
/fork              Branch current conversation
/merge id1 id2     Merge conversations together
/attach id         Import another session's context
/remember k: val   Save knowledge across sessions
```

### Cost control

```bash
relayos cost report
# Today: $0.023 / $1.00
# This month: $0.187 / $10.00
```

### Session management

```bash
/help              Show all commands
/new               New conversation
/clear             Clear messages
Ctrl+P             Command palette
Tab                Cycle provider
Shift+Tab          Cycle mode
```

---

## 🖥️ The TUI

```
┌─ RelayOS  sess-31  [Mimo]  [AUTO]  $0.02 ─┐
│                                              │
│  > 设计一个支付系统                            │
│                                              │
│  [Mimo] 建议使用事件溯源架构，原因如下：        │
│    1. 幂等性天然保证                          │
│    2. 审计日志免费获得                         │
│                                              │
├──────────────────────────────────────────────┤
│ > 帮我修一下审查问题█                           │
│  Ctrl+P=palette  Tab=provider  /fork  /merge  │
└──────────────────────────────────────────────┘
```

| Shortcut | What |
|----------|------|
| `Ctrl+P` | Command palette (all settings) |
| `Tab` | Cycle through installed CLI providers |
| `Shift+Tab` | Cycle mode: auto → edit → group |
| `Enter` | Send message / Confirm |
| `↑/↓` | Input / history navigation |
| `Esc` | Cancel / clear input |
| `Backspace` | Delete character |
| `Ctrl+U` | Clear input line |
| `Ctrl+C` | Exit

### Command palette (Ctrl+P)

```
  Command Palette  (Esc close)
  ────────────────────────────────────────────────
  Session:
    New Session            Start fresh conversation
    Fork Session           Branch from current session
    Merge Sessions         Combine multiple sessions
    Switch Session         Browse all sessions
    Attach Session         Import context from another session
  Knowledge:
    Remember Fact          Save knowledge: /remember key: value
    Browse Knowledge       Explore stored facts
  Settings:
    Toggle Mode            Auto / Edit / Group
    Budget                 Spending limits
  System:
    Quit                   Exit RelayOS
  Filter: (type to filter)
  Up/Down | Enter | Esc
```

### Switch Session Panel (Ctrl+P → Switch Session)

```
  Sessions  (Esc to close)
  ────────────────────────────────────────────────
  > Search: |                    ← Tab to switch
    conv-payment    [Mimo]     2m
     设计一个支付系统...
    conv-review     [Claude]   30m
     Review PR for security...
  
  Tab=switch  ↑↓=navigate  Enter=open  d=delete  Esc=close
```

### Conversation Graph View

```
Conversation Graph
────────────────────────────────────────────────
└── Payment Design
    └── Architecture v1
        ├── Architecture v2
        └── > Final Arch
                ▲
                │
└── Cache Layer ────────────────────┘
```

---

## 🗺️ Architecture

```
Terminal (relay / relayos)
         │
         ▼
┌──────────────────────────────────────────────┐
│            Conversation Graph                │
│  (fork / merge / attach / session lifecycle) │
└──────────────────┬───────────────────────────┘
                   │
┌──────────────────▼───────────────────────────┐
│              ProviderRouter                  │
│  (weighted routing, auto/edit mode, budget)  │
└──────┬──────────────────────┬────────────────┘
       │                      │
┌──────▼──────┐     ┌─────────▼──────────┐
│  API Prov. │     │  CLI Provider       │
│  OpenAI    │     │  claude / opencode  │
│  Anthropic │     │  mimo / codex       │
│  Google    │     │  (auto-detected)    │
│  DeepSeek  │     └────────────────────┘
└─────────────┘
```

### Storage (all SQLite, zero infrastructure)

```
~/.relayos/
├── config.yaml       ← Your provider config
├── sessions.db       ← Sessions + conversation graph
├── knowledge.db      ← Cross-session memory
├── cost.db           ← Usage + spending
├── state.db          ← Project facts + decisions
├── artifacts.db      ← Structured outputs
├── workers.db        ← Worker definitions
└── inbox.db          ← Messages
```

### Design Philosophy

| Principle | Why |
|-----------|-----|
| **Conversation Graph** | Fork/merge conversations like code. Git for AI. |
| **Zero config** | Auto-detect installed AI CLIs. No API keys required. |
| **Budget-first** | Hard spending limits. No surprise bills. |
| **Auto by default** | Workers auto-assigned. Provider names hidden. |
| **i18n native** | Chinese + English. Auto-detect system language. |

---

## 📈 Version History

| Version | What |
|---------|------|
| **V0.1** | Model routing — 5 provider adapters |
| **V0.2** | Terminal pool — multi-CLI, cost tracking |
| **V0.3** | Worker system — 8 roles, persistence, TUI |
| **V0.4** | State compiler — structured state, event sourcing |
| **V0.5** | Model scheduler — 15 models, 3 cost profiles |
| **V0.6** | Session system — chat/ask/group modes |
| **V0.7** | Capability graph — multi-step decomposition |
| **V0.8** | Task graph execution — schema-aware artifact passing |
| **V0.9** | Cross-session memory — project knowledge |
| **V0.10** | Unified Provider — API + CLI abstraction |
| **V0.11** | Conversation Graph — fork/merge/attach |
| **V0.12** | OpenCode-style TUI + Graph View + BudgetGuard |

---

## 💪 Built With

| Component | Tech |
|-----------|------|
| **Language** | Python 3.10+ |
| **CLI + TUI** | Click + Rich |
| **HTTP Client** | HTTPX |
| **Storage** | SQLite (zero infra) |
| **License** | Apache 2.0 |

### Credits

- **Claude Code** (Anthropic) — Primary development platform
- **OpenCode** — TUI design inspiration
- **ECC plugin system** — Agent orchestration patterns

---

## 📦 Installation

```bash
pip install relayos
```

### From source

```bash
git clone https://github.com/jjjjjjjjnnjnn/relayos.git
cd relayos
pip install -e .
```

### Optional: web dashboard

```bash
pip install relayos[server]
relayos serve --open
```

---

## 🌐 Languages

- [English](README.md)
- [中文 (Chinese)](README_ZH.md)
- [Deutsch (German)](README_DE.md)
- [Français (French)](README_FR.md)
- [Español (Spanish)](README_ES.md)
- [日本語 (Japanese)](README_JP.md)
- [한국어 (Korean)](README_KR.md)

---

## 📄 License

[Apache 2.0](LICENSE) Copyright 2026 [jjjjjjjjnnjnn](https://github.com/jjjjjjjjnnjnn)

---

<p align="center">
  <strong>Stop copy-pasting between AI tools.<br>
  Fork, merge, and weave conversations together.</strong><br>
  <br>
  <a href="https://github.com/jjjjjjjjnnjnn/relayos"><img src="https://img.shields.io/badge/GitHub-★-181717?style=for-the-badge&logo=github" alt="GitHub"></a>
  <a href="#-quick-start"><img src="https://img.shields.io/badge/Get_Started-10B981?style=for-the-badge" alt="Get Started"></a>
  <br>
  <sub><code>pip install relayos && relay</code></sub>
</p>
