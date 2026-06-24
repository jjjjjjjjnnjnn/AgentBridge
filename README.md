<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/RelayOS-v0.2.0a12-8B5CF6?style=for-the-badge" alt="RelayOS">
  </picture>
</p>

<h1 align="center">RelayOS</h1>

<p align="center">
  <strong>Git for AI Conversations.</strong><br>
  <br>
  Fork, merge, and weave AI conversations together.<br>
  One workspace for Claude, GPT, Gemini, DeepSeek, and local models.
</p>

<p align="center">
  <a href="#-quick-start"><img src="https://img.shields.io/badge/Quick_Start-10B981?style=for-the-badge" alt="Quick Start"></a>
  <a href="#%EF%B8%8F-features"><img src="https://img.shields.io/badge/Features-3B82F6?style=for-the-badge" alt="Features"></a>
  <a href="https://github.com/jjjjjjjjnnjnn/relayos"><img src="https://img.shields.io/badge/GitHub-181717?style=for-the-badge&logo=github" alt="GitHub"></a>
  <a href="#-installation"><img src="https://img.shields.io/badge/pip_install_relayos-FF6F00?style=for-the-badge&logo=pypi" alt="Install"></a>
</p>

<p align="center">
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
| 🧠 **Auto Routing** | Free models first, premium only when needed |
| 💰 **Budget Guard** | Per-task/daily/monthly hard limits, no surprise bills |
| 🔌 **Unified Provider** | API + CLI — zero-config, auto-detect installed tools |
| ⌨️ **OpenCode-Style TUI** | Ctrl+P command palette, Tab switch, Chat interface |
| 💾 **Cross-Session Memory** | `/remember` facts that persist across conversations |
| 🌐 **i18n** | Chinese + English auto-detect |
| 🚀 **Auto/Edit Mode** | Auto (no ask) or Edit (confirm before each call) |

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
Ctrl+X S           Session list
Ctrl+X G           Conversation graph
```

---

## 🖥️ The TUI

```
┌─ RelayOS  sess-31  Derived: #12 #25  [AUTO]  $0.02 ─┐
│                                                       │
│  > 设计一个支付系统                                     │
│                                                       │
│  [architect] 建议使用事件溯源架构，原因如下：           │
│    1. 幂等性天然保证                                   │
│    2. 审计日志免费获得                                 │
│                                                       │
│  [reviewer] 发现2个安全问题：                          │
│    JWT未设过期时间、缺少速率限制                        │
│                                                       │
├───────────────────────────────────────────────────────┤
│ > 帮我修一下审查问题█                                    │
│  Ctrl+P=palette  /fork  /merge  /remember  /help      │
└───────────────────────────────────────────────────────┘
```

| Shortcut | What |
|----------|------|
| `Ctrl+P` | Command palette (all settings) |
| `Ctrl+X N` | New session |
| `Ctrl+X S` | Session list |
| `Ctrl+X G` | Conversation graph |
| `Ctrl+X M` | Toggle auto/edit mode |
| `Ctrl+X C` | Cost report |
| `Tab` | Switch provider |
| `Esc` | Cancel / clear input |
| `Up/Down` | Input history |

### Command palette (Ctrl+P)

```
Command Palette
────────────────────────────────────────────────
Session:
  New Session          (Ctrl+X N)  Start fresh
  Fork Session         (/fork)     Branch current
  Merge Sessions       (/merge)    Combine sessions
  Switch Session       (Ctrl+X S)  Browse all
  Attach Session       (/attach)   Import context
Knowledge:
  Remember Fact        (/remember) Save knowledge
  Browse Knowledge     (Ctrl+X K)  Explore facts
Settings:
  Toggle Mode          (Ctrl+X M)  Auto / Edit
  Budget               (Ctrl+X C)  Spending
Tools:
  Conversation Graph   (Ctrl+X G)  Visual tree
System:
  Help                 (Ctrl+X ?)
  Quit                 (Ctrl+C)
```

### Conversation Graph View (Ctrl+X G)

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
