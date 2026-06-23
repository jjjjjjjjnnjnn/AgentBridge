<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/AgentBridge-v0.1.0a1-8B5CF6?style=for-the-badge" alt="AgentBridge">
  </picture>
</p>

<h1 align="center">AgentBridge</h1>

<p align="center">
  <strong>告别在 AI 工具之间复制粘贴。</strong><br>
  在 Claude、GPT、Gemini、DeepSeek 和本地模型之间创建持久的 AI 工作线程——<br>
  配备共享内存、工作流编排和 MCP 集成。
</p>

<p align="center">
  <a href="#-快速开始"><img src="https://img.shields.io/badge/-快速开始-10B981?style=flat-square" alt="快速开始"></a>
  <a href="#-功能特性"><img src="https://img.shields.io/badge/-功能特性-3B82F6?style=flat-square" alt="功能特性"></a>
  <a href="#%EF%B8%8F-配置"><img src="https://img.shields.io/badge/-配置-8B5CF6?style=flat-square" alt="配置"></a>
  <a href="#-示例"><img src="https://img.shields.io/badge/-示例-F59E0B?style=flat-square" alt="示例"></a>
  <a href="#%EF%B8%8F-架构"><img src="https://img.shields.io/badge/-架构-EC4899?style=flat-square" alt="架构"></a>
  <a href="#%EF%B8%8F-致谢"><img src="https://img.shields.io/badge/-致谢-6366F1?style=flat-square" alt="致谢"></a>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文-文档-EA4335?style=flat-square" alt="中文"></a>
  <a href="README_DE.md"><img src="https://img.shields.io/badge/Deutsch-Dokument-FFD700?style=flat-square" alt="Deutsch"></a>
  <a href="README_ES.md"><img src="https://img.shields.io/badge/Español-Doc-00C853?style=flat-square" alt="Español"></a>
  <a href="README_FR.md"><img src="https://img.shields.io/badge/Français-Doc-1E90FF?style=flat-square" alt="Français"></a>
  <a href="README_JP.md"><img src="https://img.shields.io/badge/日本語-ドキュメント-FF4081?style=flat-square" alt="日本語"></a>
  <a href="README_KR.md"><img src="https://img.shields.io/badge/한국어-문서-03C75A?style=flat-square" alt="한국어"></a>
</p>

---

## 📋 目录

| 章节 | 说明 |
|---------|-------------|
| [🎯 概述](#-概述) | AgentBridge 是什么以及为何存在 |
| [✨ 功能特性](#-功能特性) | 当前能力 |
| [⚡ 快速开始](#-快速开始) | 安装并运行你的第一个工作流 |
| [📖 使用指南](#-使用指南) | 工作流、终端、内存 |
| [⚙️ 配置](#%EF%B8%8F-配置) | 提供商、终端、路由 |
| [🏗️ 架构](#%EF%B8%8F-架构) | 系统设计 |
| [📁 示例](#-示例) | 可直接使用的工作流 |
| [🛣️ 路线图](#%EF%B8%8F-路线图) | 未来规划 |
| [🙏 致谢](#%EF%B8%8F-致谢) | 鸣谢 |
| [📄 许可证](#-许可证) | MIT |

---

## 🎯 概述

**AgentBridge** 是一个面向 AI 智能体的开源协调层——就像 Docker 之于容器，但服务于 AI 工具。

### 问题

你使用 **Claude Code** 做架构设计，**ChatGPT** 做推理，**Gemini** 做研究，**DeepSeek** 写代码。每个工具都很出色，但 **它们之间无法互通。** 你浪费了 30% 的时间在不同工具之间复制粘贴上下文，并用高价模型处理免费模型就能完成的任务。

### 解决方案

```
┌─────────────────────────────────────────────────────┐
│                   你的 AI 工具                         │
│   Claude Code    ChatGPT    Gemini    DeepSeek       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   AgentBridge                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   终端池     │  │  工作流引擎  │  │   共享内存   │  │
│  │ (多 CLI)    │  │  (YAML)     │  │  (SQLite)   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │   适配器     │  │ MCP 客户端  │                    │
│  │ (5 提供商)  │  │  (工具)     │                    │
│  └─────────────┘  └─────────────┘                    │
└──────────────────────────────────────────────────────┘
```

---

## ✨ 功能特性

### 🤖 多终端池
- 在同一 CLI 工具中**同时运行多个实例**（例如 3 个 Claude Code 终端）
- 每个终端拥有**独立的模型选择**
- 跨会话**持久化**（基于 SQLite）

**支持的终端：** `claude`、`mimo`、`opencode`、`codex`、`qcode`、`custom`

### 🔄 工作流引擎
- **顺序**管道——步骤之间支持模板变量解析
- **并行**执行——在多个终端上同时运行
- YAML 定义的工作流——无需编写代码

### 🧠 共享内存
- **跨智能体上下文**：每个智能体可以看到前序智能体的输出
- **SQLite 持久化**：内存数据跨会话保留
- **命名键**：使用 `save_as` 进行语义引用

### 🔗 MCP 集成
- 连接**任意 MCP 服务器**以获取工具
- 基于标准输入的 MCP 客户端，支持超时和错误处理

### 💰 成本感知路由（规划中）
- 优先使用免费模型，仅在必要时使用付费模型
- 按策略路由（质量优先 vs 速度优先 vs 成本优先）

---

## ⚡ 快速开始

### 安装

```bash
pip install agentbridge
```

### 初始化

```bash
agentbridge init
```

通过环境变量配置 API 密钥：

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export DEEPSEEK_API_KEY="sk-..."
```

### 运行你的第一个工作流

创建文件 `hello.yaml`:

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

执行它：

```bash
agentbridge run hello.yaml
```

### 管理终端

```bash
# 查看可用终端类型
agentbridge terminal types

# 创建一个用于架构设计的 Claude Code 终端
agentbridge terminal create claude -n architect -m claude-sonnet-4-20250514

# 再创建一个用于快速任务的终端
agentbridge terminal create claude -n assistant -m claude-haiku-4-20251001

# 创建一个用于研究的 Gemini 终端
agentbridge terminal create google -n researcher -m gemini-2.5-flash

# 查看所有运行中的终端
agentbridge terminal list

# 在指定终端上运行提示
agentbridge terminal exec opencode "Analyze this data"
```

---

## 📖 使用指南

### 工作流

工作流是定义多智能体管道的 YAML 文件：

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

| 字段 | 说明 |
|-------|-------------|
| `agent` | 使用的终端类型（claude、gemini、gpt、opencode、deepseek） |
| `prompt` | 要发送的提示内容 |
| `save_as` | 将结果存入共享内存的键名 |
| `system` | 系统提示（可选） |
| `model` | 模型覆盖（可选） |
| `parallel` | 设为 `true` 以在并行组中运行此步骤 |

### 终端

AgentBridge 将每个 AI CLI 视为一个"终端"——独立运行的工作线程：

| 终端 | 二进制 | 默认模型 | 状态 |
|----------|--------|---------------|--------|
| `claude` | `claude` | claude-sonnet-4-20250514 | ✅ 可用 |
| `mimo` | `mimo` | gpt-4o | ✅ 可用 |
| `opencode` | `opencode` | deepseek-chat | ✅ 可用 |
| `codex` | `codex` | gpt-4o | ❌ 未安装 |
| `qcode` | `q` | qwen2.5:7b | ❌ 未安装 |
| `custom` | (可配置) | 用户自定义 | ⚡ 自定义 |

### 共享内存

```bash
# 存储
agentbridge remember my_key "some value"

# 检索
agentbridge recall my_key

# 列出所有键
agentbridge memory-list
```

---

## ⚙️ 配置

配置文件位置：`~/.agentbridge/config.yaml`（或 `$AGENTBRIDGE_CONFIG_DIR/config.yaml`）

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

**API 密钥优先级：**
1. 配置文件中的 `api_key` 字段
2. 环境变量（`OPENAI_API_KEY`、`ANTHROPIC_API_KEY` 等）
3. 空值（适配器会发出警告）

---

## 🏗️ 架构

```
                    ┌─────────────────────┐
                    │   CLI (Click)       │
                    │  agentbridge run     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   AgentBridge Core    │
                    │                      │
                    │  ┌────────────────┐  │
                    │  │   终端池         │──│──→ Claude Code, Mimo, OpenCode...
                    │  │  (多实例)       │  │
                    │  ├────────────────┤  │
                    │  │  工作流引擎      │  │
                    │  │  (YAML 解析器)  │  │
                    │  ├────────────────┤  │
                    │  │   调度器         │──│──→ 顺序 / 并行
                    │  ├────────────────┤  │
                    │  │   共享内存       │  │
                    │  │   (SQLite)      │  │
                    │  ├────────────────┤  │
                    │  │    适配器        │──│──→ OpenAI / Claude / Gemini...
                    │  ├────────────────┤  │
                    │  │  MCP 客户端     │──│──→ GitHub MCP / Filesystem MCP...
                    │  └────────────────┘  │
                    └──────────────────────┘
```

### 设计决策

| 决策 | 选择 | 理由 |
|----------|--------|-----------|
| CLI 优先 | Click + YAML | 零代码工作流；非开发人员也能创建管道 |
| 多实例 | 线程池 | 在多个模型上同时运行智能体 |
| 持久化 | SQLite | 跨会话内存，无需外部依赖 |
| 适配器 | 基于 httpx | 最小化依赖；无需提供商 SDK |
| MCP | 仅客户端（v0.1） | 消费 MCP 服务器；v1.0 支持 Hub 模式 |

---

## 📁 示例

| 示例 | 说明 |
|---------|-------------|
| `examples/saas-builder.yaml` | 4 智能体 SaaS 设计管道：Gemini 研究 → Claude 设计 → GPT 编码 → DeepSeek 审查 |
| `examples/linguagraph-research.yaml` | 3 智能体研究管道：语言分析 → 认知模型 → 论文撰写 |
| `examples/debate.yaml` | 3 智能体辩论：本地 vs 云端 LLM，由 Gemini 评判 |
| `examples/parallel-research.yaml` | 4 智能体并行研究冲刺，带综合汇总 |

---

## 🛣️ 路线图

- **v0.1** — ✅ CLI、YAML 工作流、5 个适配器、共享内存、MCP 客户端、终端池
- **v0.2** — 🔄 Web 仪表盘（Next.js）、工作流可视化、成本感知路由、Docker
- **v0.5** — 🔄 LangGraph 编排、条件分支、人工参与（Human-in-the-loop）
- **v1.0** — 🔄 双向 MCP Hub、插件系统、向量内存

---

## 🙏 致谢

AgentBridge 站在巨人的肩膀上。我们向以下项目致以最深切的感谢：

### 🖥️ 终端平台

| 平台 | 致谢 |
|----------|--------|
| **[Claude Code](https://claude.ai)** — 由 Anthropic 提供支持 | 主要开发平台。AgentBridge 使用 Claude Code 的智能体编排能力进行设计和构建。[条款](https://www.anthropic.com/legal) · [隐私](https://www.anthropic.com/privacy) |
| **[OpenCode](https://opencode.ai)** | 终端适配器目标和测试伙伴。OpenCode CLI 提供 AgentBridge 终端池使用的运行接口。 |
| **[MimoCode](https://mimo.ai)** | 终端适配器目标。Mimo 的 CLI 集成支持多模型前端工作流。 |
| **OpenAI Codex** | 编码类任务的终端适配器目标。 |

### 🤖 开发中使用的 AI 模型

- **Claude Opus 4.8 / Sonnet 4.6**（Anthropic）— 主要开发模型
- **Gemini 2.5 Flash**（Google）— 研究任务、竞品分析
- **GPT-4o**（OpenAI）— 架构评估与审查
- **DeepSeek V3**（DeepSeek）— 代码审查与测试

### 📦 开源依赖

| 依赖 | 许可证 | 用途 |
|------------|---------|---------|
| [Click](https://palletsprojects.com/p/click/) | BSD-3-Clause | CLI 框架 |
| [PyYAML](https://pyyaml.org/) | MIT | YAML 解析 |
| [HTTPX](https://www.python-httpx.org/) | BSD-3-Clause | 模型 API 的 HTTP 客户端 |
| [pydantic](https://docs.pydantic.dev/)（规划中） | MIT | 配置验证（v0.2） |

### 🧠 技能与知识来源

- **ECC（Engineering Claude Code）** 插件系统——智能体编排模式
- **Claude Scholar**——学术研究工作流模式
- **MCP（Model Context Protocol）**——Anthropic 的工具集成协议

### 🌍 社区翻译

AgentBridge README 提供以下语言版本：
- [中文 (Chinese)](README_ZH.md)
- [Deutsch (German)](README_DE.md)
- [Français (French)](README_FR.md)
- [Español (Spanish)](README_ES.md)
- [日本語 (Japanese)](README_JP.md)
- [한국어 (Korean)](README_KR.md)

---

## 📄 许可证

[MIT](LICENSE) © 2026 [jjjjjjjjnnjnn](https://github.com/jjjjjjjjnnjnn)

---

<p align="center">
  <strong>AgentBridge</strong> — AI 智能体的协调层。<br>
  <sub>为开源 AI 社区用心打造 ❤️</sub>
</p>
