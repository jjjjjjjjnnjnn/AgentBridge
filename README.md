<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/AgentBridge-v0.1.0a1-8B5CF6?style=for-the-badge" alt="AgentBridge">
  </picture>
</p>

<h1 align="center">AgentBridge</h1>

<p align="center">
  <strong>Stop copy-pasting between AI tools.</strong><br>
  Create persistent AI workers across Claude, GPT, Gemini, DeepSeek and local models —<br>
  with shared memory, workflow orchestration, and MCP integration.
</p>

<p align="center">
  <a href="#-quick-start"><img src="https://img.shields.io/badge/-Quick_Start-10B981?style=flat-square" alt="Quick Start"></a>
  <a href="#-features"><img src="https://img.shields.io/badge/-Features-3B82F6?style=flat-square" alt="Features"></a>
  <a href="#-configuration"><img src="https://img.shields.io/badge/-Configuration-8B5CF6?style=flat-square" alt="Configuration"></a>
  <a href="#-examples"><img src="https://img.shields.io/badge/-Examples-F59E0B?style=flat-square" alt="Examples"></a>
  <a href="#-architecture"><img src="https://img.shields.io/badge/-Architecture-EC4899?style=flat-square" alt="Architecture"></a>
  <a href="#%EF%B8%8F-credits"><img src="https://img.shields.io/badge/-Credits-6366F1?style=flat-square" alt="Credits"></a>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文-文档-EA4335?style=flat-square" alt="中文"></a>
  <a href="README_DE.md"><img src="https://img.shields.io/badge/Deutsch-Dokument-FFD700?style=flat-square" alt="Deutsch"></a>
  <a href="README_ES.md"><img src="https://img.shields.io/badge/Español-Doc-00C853?style=flat-square" alt="Español"></a>
  <a href="README_FR.md"><img src="https://img.shields.io/badge/Français-Doc-1E90FF?style=flat-square" alt="Français"></a>
  <a href="README_JP.md"><img src="https://img.shields.io/badge/日本語-ドキュメント-FF4081?style=flat-square" alt="日本語"></a>
  <a href="README_KR.md"><img src="https://img.shields.io/badge/한국어-문서-03C75A?style=flat-square" alt="한국어"></a>
</p>

---

## 📋 Index

| Section | Description |
|---------|-------------|
| [🎯 Overview](#-overview) | What AgentBridge is and why it exists |
| [✨ Features](#-features) | Current capabilities |
| [⚡ Quick Start](#-quick-start) | Install and run your first workflow |
| [📖 User Guide](#-user-guide) | Workflows, terminals, memory |
| [⚙️ Configuration](#%EF%B8%8F-configuration) | Providers, terminals, routing |
| [🏗️ Architecture](#%EF%B8%8F-architecture) | System design |
| [📁 Examples](#-examples) | Ready-to-use workflows |
| [🛣️ Roadmap](#%EF%B8%8F-roadmap) | Future plans |
| [🙏 Credits](#%EF%B8%8F-credits) | Acknowledgements |
| [📄 License](#-license) | MIT |

---

## 🎯 Overview

**AgentBridge** is an open-source coordination layer for AI agents — like Docker for containers, but for AI tools.

### The Problem

You use **Claude Code** for architecture, **ChatGPT** for reasoning, **Gemini** for research, **DeepSeek** for coding. Each tool is excellent. **They don't talk to each other.** You waste 30% of your time copying context between tools and burning premium tokens on tasks a free model could handle.

### The Solution

```
┌─────────────────────────────────────────────────────┐
│                   Your AI Tools                      │
│   Claude Code    ChatGPT    Gemini    DeepSeek       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   AgentBridge                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Terminal   │  │   Workflow  │  │   Shared    │  │
│  │   Pool      │  │   Engine    │  │   Memory    │  │
│  │ (Multi-CLI) │  │  (YAML)     │  │  (SQLite)   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │  Adapters   │  │ MCP Client  │                    │
│  │ (5 providers)│  │  (Tools)    │                    │
│  └─────────────┘  └─────────────┘                    │
└──────────────────────────────────────────────────────┘
```

---

## ✨ Features

### 🤖 Multi-Terminal Pool
- Run **multiple instances** of the same CLI tool (e.g., 3 Claude Code terminals simultaneously)
- Each terminal has **independent model selection**
- **Persistent** across sessions (SQLite-backed)

**Supported terminals:** `claude`, `mimo`, `opencode`, `codex`, `qcode`, `custom`

### 🔄 Workflow Engine
- **Sequential** pipelines with template variable resolution between steps
- **Parallel** execution across multiple terminals simultaneously
- YAML-defined workflows — no coding required

### 🧠 Shared Memory
- **Cross-agent context**: each agent sees previous agents' output
- **SQLite persistence**: memory survives across sessions
- **Named keys**: `save_as` for semantic reference

### 🔗 MCP Integration
- Connect to **any MCP server** for tools
- Stdio-based MCP client with timeout and error handling

### 💰 Cost-Aware Routing (planned)
- Free models first, paid only when needed
- Per-policy routing (quality vs speed vs cost)

---

## ⚡ Quick Start

### Installation

```bash
pip install agentbridge
```

### Initialize

```bash
agentbridge init
```

Configure your API keys via environment variables:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export DEEPSEEK_API_KEY="sk-..."
```

### Run Your First Workflow

Create a file `hello.yaml`:

```yaml
name: "Hello Multi-Agent"

steps:
  - agent: gemini
    prompt: "List 3 interesting facts about the MCP protocol."
    save_as: research

  - agent: claude
    prompt: "Based on: {{research}}\nDesign a simple architecture."
    save_as: architecture
```

Execute it:

```bash
agentbridge run hello.yaml
```

### Manage Terminals

```bash
# See what terminals are available
agentbridge terminal types

# Create one Claude Code terminal for architecture
agentbridge terminal create claude -n architect -m claude-sonnet-4-20250514

# And another for quick tasks
agentbridge terminal create claude -n assistant -m claude-haiku-4-20251001

# Create a Gemini terminal for research
agentbridge terminal create google -n researcher -m gemini-2.5-flash

# See all running terminals
agentbridge terminal list

# Run a prompt on a specific terminal
agentbridge terminal exec opencode "Analyze this data"
```

---

## 📖 User Guide

### Workflows

Workflows are YAML files defining multi-agent pipelines:

```yaml
name: "Pipeline Name"
description: "What this pipeline does"

vars:
  topic: "AI safety"

steps:
  - agent: gemini
    prompt: "Research {{topic}}"
    save_as: research
    system: "You are a research analyst."

  - agent: claude
    prompt: "Design based on: {{research}}"
    save_as: design
```

| Field | Description |
|-------|-------------|
| `agent` | Terminal type to use (claude, gemini, gpt, opencode, deepseek) |
| `prompt` | The prompt to send |
| `save_as` | Key to store result in shared memory |
| `system` | System prompt (optional) |
| `model` | Model override (optional) |
| `parallel` | Set `true` to run step in parallel group |

### Terminals

AgentBridge treats each AI CLI as a "terminal" — an independently running worker:

| Terminal | Binary | Default Model | Status |
|----------|--------|---------------|--------|
| `claude` | `claude` | claude-sonnet-4-20250514 | ✅ Available |
| `mimo` | `mimo` | gpt-4o | ✅ Available |
| `opencode` | `opencode` | deepseek-chat | ✅ Available |
| `codex` | `codex` | gpt-4o | ❌ Not installed |
| `qcode` | `q` | qwen2.5:7b | ❌ Not installed |
| `custom` | (configurable) | user-defined | ⚡ Custom |

### Shared Memory

```bash
# Store
agentbridge remember my_key "some value"

# Retrieve
agentbridge recall my_key

# List all keys
agentbridge memory-list
```

---

## ⚙️ Configuration

Config file location: `~/.agentbridge/config.yaml` (or `$AGENTBRIDGE_CONFIG_DIR/config.yaml`)

```yaml
providers:
  openai:
    model: gpt-4o
  anthropic:
    model: claude-sonnet-4-20250514
  google:
    model: gemini-2.5-flash
  deepseek:
    model: deepseek-chat
  ollama:
    model: qwen2.5:7b
    base_url: http://localhost:11434

terminals:
  - name: claude-main
    type: claude
    model: claude-sonnet-4-20250514
  - name: claude-fast
    type: claude
    model: claude-haiku-4-20251001
  - name: mimo-coder
    type: mimo
    model: gpt-4o

routing:
  default: balanced
  policies:
    coding: free_first
    research: quality_first
    quick: cheapest
```

**API Key Precedence:**
1. Config file `api_key` field
2. Environment variable (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
3. Empty (adapter will warn)

---

## 🏗️ Architecture

```
                    ┌─────────────────────┐
                    │    CLI (Click)       │
                    │  agentbridge run     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   AgentBridge Core    │
                    │                      │
                    │  ┌────────────────┐  │
                    │  │  Terminal Pool  │──│──→ Claude Code, Mimo, OpenCode...
                    │  │  (Multi-Inst.)  │  │
                    │  ├────────────────┤  │
                    │  │ Workflow Engine │  │
                    │  │  (YAML Parser)  │  │
                    │  ├────────────────┤  │
                    │  │   Scheduler     │──│──→ Sequential / Parallel
                    │  ├────────────────┤  │
                    │  │  Shared Memory  │  │
                    │  │   (SQLite)      │  │
                    │  ├────────────────┤  │
                    │  │    Adapters     │──│──→ OpenAI / Claude / Gemini...
                    │  ├────────────────┤  │
                    │  │   MCP Client    │──│──→ GitHub MCP / Filesystem MCP...
                    │  └────────────────┘  │
                    └──────────────────────┘
```

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI-first | Click + YAML | Zero-code workflows; non-developers can create pipelines |
| Multi-instance | Thread pool | Run concurrent agents on different models |
| Persistence | SQLite | Cross-session memory with no external dependency |
| Adapters | httpx-based | Minimal dependencies; no provider SDKs |
| MCP | Client-only (v0.1) | Consume MCP servers; Hub mode in v1.0 |

---

## 📁 Examples

| Example | Description |
|---------|-------------|
| `examples/saas-builder.yaml` | 4-agent SaaS design pipeline: Gemini research → Claude design → GPT code → DeepSeek review |
| `examples/linguagraph-research.yaml` | 3-agent research pipeline: linguistic analysis → cognitive model → paper writing |
| `examples/debate.yaml` | 3-agent debate: pro-local vs pro-cloud LLM, judged by Gemini |
| `examples/parallel-research.yaml` | 4-agent parallel research sprint with synthesis |

---

## 🛣️ Roadmap

- **v0.1** — ✅ CLI, YAML workflows, 5 adapters, shared memory, MCP client, terminal pool
- **v0.2** — 🔄 Web Dashboard (Next.js), Workflow visualization, Cost-aware routing, Docker
- **v0.5** — 🔄 LangGraph orchestration, Conditional branching, Human-in-the-loop
- **v1.0** — 🔄 Bidirectional MCP Hub, Plugin system, Vector memory

---

## 🙏 Credits

AgentBridge is built on the shoulders of giants. We extend our deepest gratitude to:

### 🖥️ Terminal Platforms

| Platform | Credit |
|----------|--------|
| **[Claude Code](https://claude.ai)** — Powered by Anthropic | The primary development platform. AgentBridge was designed and built using Claude Code's agent orchestration capabilities. [Terms](https://www.anthropic.com/legal) · [Privacy](https://www.anthropic.com/privacy) |
| **[OpenCode](https://opencode.ai)** | Terminal adapter target and testing partner. OpenCode CLI provides the run interface used by AgentBridge's terminal pool. |
| **[MimoCode](https://mimo.ai)** | Terminal adapter target. Mimo's CLI integration enables multi-model frontend workflows. |
| **OpenAI Codex** | Terminal adapter target for coding-specific tasks. |

### 🤖 AI Models Used in Development

- **Claude Opus 4.8 / Sonnet 4.6** (Anthropic) — Primary development models
- **Gemini 2.5 Flash** (Google) — Research tasks, competitive analysis
- **GPT-4o** (OpenAI) — Architecture evaluation and review
- **DeepSeek V3** (DeepSeek) — Code review and testing

### 📦 Open Source Dependencies

| Dependency | License | Purpose |
|------------|---------|---------|
| [Click](https://palletsprojects.com/p/click/) | BSD-3-Clause | CLI framework |
| [PyYAML](https://pyyaml.org/) | MIT | YAML parsing |
| [HTTPX](https://www.python-httpx.org/) | BSD-3-Clause | HTTP client for model APIs |
| [pydantic](https://docs.pydantic.dev/) (planned) | MIT | Config validation (v0.2) |

### 🧠 Skills & Knowledge Sources

- **ECC (Engineering Claude Code)** plugin system — agent orchestration patterns
- **Claude Scholar** — academic research workflow patterns
- **MCP (Model Context Protocol)** — Anthropic's protocol for tool integration

### 🌍 Community Translations

AgentBridge README is available in:
- [中文 (Chinese)](README_ZH.md)
- [Deutsch (German)](README_DE.md)
- [Français (French)](README_FR.md)
- [Español (Spanish)](README_ES.md)
- [日本語 (Japanese)](README_JP.md)
- [한국어 (Korean)](README_KR.md)

---

## 📄 License

[MIT](LICENSE) © 2026 [jjjjjjjjnnjnn](https://github.com/jjjjjjjjnnjnn)

---

<p align="center">
  <strong>AgentBridge</strong> — The coordination layer for AI agents.<br>
  <sub>Built with ❤️ for the open-source AI community</sub>
</p>
