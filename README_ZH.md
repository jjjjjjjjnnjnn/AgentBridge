<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/RelayOS-v0.2.0a12-8B5CF6?style=for-the-badge" alt="RelayOS">
  </picture>
</p>

<h1 align="center">RelayOS</h1>

<p align="center">
  <strong>AI 对话的 Git。</strong><br>
  <br>
  Fork、merge、串联你的 AI 对话。<br>
  一个工作空间整合 Claude、GPT、Gemini、DeepSeek 和本地模型。
</p>

<p align="center">
  <a href="#-快速开始"><img src="https://img.shields.io/badge/快速开始-10B981?style=for-the-badge" alt="快速开始"></a>
  <a href="#-安装"><img src="https://img.shields.io/badge/pip_install_relayos-FF6F00?style=for-the-badge&logo=pypi" alt="安装"></a>
</p>

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/English-FFFFFF?style=flat-square" alt="English"></a>
  <a href="README_DE.md"><img src="https://img.shields.io/badge/Deutsch-FFD700?style=flat-square" alt="Deutsch"></a>
  <a href="README_ES.md"><img src="https://img.shields.io/badge/Español-00C853?style=flat-square" alt="Español"></a>
  <a href="README_FR.md"><img src="https://img.shields.io/badge/Français-1E90FF?style=flat-square" alt="Français"></a>
  <a href="README_JP.md"><img src="https://img.shields.io/badge/日本語-FF4081?style=flat-square" alt="日本語"></a>
  <a href="README_KR.md"><img src="https://img.shields.io/badge/한국어-03C75A?style=flat-square" alt="한국어"></a>
</p>

---

## 👋 问题

你在 ChatGPT、Claude、Gemini 之间来回切换，把输出从一个复制粘贴到另一个。会话之间的上下文丢失。**你花了 30% 的时间管理工具，而不是真正做事。**

有价值的对话——系统设计、架构评审——被锁定在单个会话里。无法分支、合并，也无法在之后继续构建。

## 🎯 解决方案

**RelayOS 把 AI 对话当代码来管理。** Fork、merge、串联。

```
#12 数据库设计                          #25 API设计
       │                                    │
       ├── /fork → #18 数据库v2              │
       │                                    │
       └────────── /merge ──────────────────┘
                            │
                            ▼
                         #31 系统架构
                        （衍生自 #12 #25）
```

**零配置。** 自动检测你已安装的 AI CLI 终端。

```
pip install relayos && relay
```

---

## ✨ 核心功能

| 功能 | 说明 | 收益 |
|------|------|------|
| 🔀 **对话图** | `/fork` `/merge` `/attach` | Git 级别的会话版本管理 |
| 🧠 **自动路由** | 免费模型优先，必要时用付费 | 省钱，不用操心 |
| 💰 **预算保护** | 单次/每日/每月硬上限 | 无意外账单 |
| 🔌 **统一 Provider** | API + CLI 零配置，自动检测已装工具 | 即装即用 |
| ⌨️ **OpenCode 风格 TUI** | Ctrl+P 命令面板，Tab 切换，聊天界面 | 零学习成本 |
| 💾 **跨会话记忆** | `/remember` 保存事实，跨会话持久 | 不再重复提问 |
| 🌐 **国际化** | 中文 + 英文自动检测 | 母语体验 |
| 🚀 **自动/手动模式** | auto 直接执行，edit 每次确认 | 灵活可控 |

---

## ⚡ 快速开始

```bash
pip install relayos
relay
```

打开工作台，直接打字，按 Enter。

**无需配置。** 自动检测已安装的 AI CLI（claude、opencode、mimo 等）。如果没检测到，引导向导会帮你设置。

### 一句话任务

```bash
relay "设计一个支付系统"        # 自动路由到最佳 Worker
relay "帮我审查这段代码"        # 自动识别意图
relay "解释 Kubernetes"        # 单聊
```

### 对话分支

```
/fork             分支当前对话，生成变体
/merge id1 id2    合并多个对话为集成会话
/attach id        导入另一个会话的上下文
/remember k: val  保存知识到项目记忆
```

### 消费控制

```bash
relayos cost report
# 今日：$0.023 / $1.00
# 本月：$0.187 / $10.00
```

### 会话管理

```bash
/help             查看所有命令
/new              新建会话
/clear            清空消息
Ctrl+P            命令面板（所有设置入口）
Ctrl+X S          对话列表
Ctrl+X G          对话关系图
```

---

## 🖥️ 界面

```
┌─ RelayOS  sess-31  衍生自 #12 #25  [AUTO]  $0.02 ─┐
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
│  Ctrl+P=面板  /fork  /merge  /remember  /help         │
└───────────────────────────────────────────────────────┘
```

### 快捷键

| 按键 | 功能 |
|------|------|
| `Ctrl+P` | 命令面板（所有设置） |
| `Ctrl+X N` | 新会话 |
| `Ctrl+X S` | 会话列表 |
| `Ctrl+X G` | 对话关系图 |
| `Ctrl+X M` | 切换 auto/edit 模式 |
| `Ctrl+X C` | 消费报告 |
| `Tab` | 切换 Provider |
| `Esc` | 取消 / 清空输入 |
| `↑↓` | 输入历史 |

### 命令面板（Ctrl+P）

```
命令面板
────────────────────────────────────────────────
Session:
  新会话               (Ctrl+X N)
  Fork 分支            (/fork)      分支当前会话
  Merge 合并           (/merge)     合并多个会话
  切换会话             (Ctrl+X S)
  Attach 附加          (/attach)    导入上下文
Knowledge:
  记住事实             (/remember)  保存知识
  浏览知识             (Ctrl+X K)   查看存储的事实
Settings:
  切换模式             (Ctrl+X M)   Auto / Edit
  预算                 (Ctrl+X C)   消费上限
Tools:
  对话关系图           (Ctrl+X G)   可视化树形图
System:
  帮助                 (Ctrl+X ?)
  退出                 (Ctrl+C)
```

### 对话关系图（Ctrl+X G）

```
对话关系图
────────────────────────────────────────────────
└── 支付系统设计
    └── 架构 v1
        ├── 架构 v2
        └── > 最终架构
                ▲
                │
└── 缓存层 ────────────────┘
```

---

## 🗺️ 架构

```
终端 (relay / relayos)
     │
     ▼
┌──────────────────────────────────────┐
│           对话图                      │
│  (fork / merge / attach / 会话管理)   │
└──────────────┬───────────────────────┘
               │
┌──────────────▼───────────────────────┐
│         ProviderRouter               │
│  (权重路由、auto/edit 模式、预算)     │
└──────┬──────────────┬────────────────┘
       │              │
┌──────▼──────┐ ┌─────▼──────────┐
│  API Provider │ CLI Provider    │
│  OpenAI      │ claude/opencode │
│  Anthropic   │ mimo/codex      │
│  Google      │ (自动检测)       │
│  DeepSeek    │                 │
└──────────────┘ └────────────────┘
```

### 存储（全部 SQLite，零基础设施）

```
~/.relayos/
├── config.yaml       ← Provider 配置
├── sessions.db       ← 会话 + 对话关系图
├── knowledge.db      ← 跨会话记忆
├── cost.db           ← 使用量 + 消费
├── state.db          ← 项目事实 + 决策
├── artifacts.db      ← 结构化输出
├── workers.db        ← Worker 定义
└── inbox.db          ← 消息
```

### 设计理念

| 原则 | 原因 |
|------|------|
| **对话图** | Fork/merge 会话就像管理代码。AI 对话的 Git。 |
| **零配置** | 自动检测已安装的 AI CLI。无需 API Key。 |
| **预算优先** | 硬性消费上限。无意外账单。 |
| **自动默认** | Worker 自动分配。Provider 名称隐藏。 |
| **原生国际化** | 中文 + 英文，自动检测系统语言。 |

---

## 📈 版本历史

| 版本 | 内容 |
|------|------|
| **V0.1** | 模型路由 — 5 个 Provider 适配器 |
| **V0.2** | 终端池 — 多 CLI、成本追踪 |
| **V0.3** | Worker 系统 — 8 角色、持久化、TUI |
| **V0.4** | 状态编译器 — 结构化状态、事件溯源 |
| **V0.5** | 模型调度器 — 15 模型、3 成本配置 |
| **V0.6** | 会话系统 — chat/ask/group 模式 |
| **V0.7** | 能力图 — 多步任务分解 |
| **V0.8** | 任务图执行 — schema 感知产物传递 |
| **V0.9** | 跨会话记忆 — 项目知识库 |
| **V0.10** | 统一 Provider — API + CLI 抽象 |
| **V0.11** | 对话图 — fork/merge/attach |
| **V0.12** | OpenCode 风格 TUI + 图可视化 + 预算保护 |

---

## 💪 技术栈

| 组件 | 技术 |
|------|------|
| **语言** | Python 3.10+ |
| **CLI + TUI** | Click + Rich |
| **HTTP 客户端** | HTTPX |
| **存储** | SQLite（零基础设施） |
| **许可证** | Apache 2.0 |

---

## 📦 安装

```bash
pip install relayos
```

### 源码安装

```bash
git clone https://github.com/jjjjjjjjnnjnn/relayos.git
cd relayos
pip install -e .
```

### 可选：Web 面板

```bash
pip install relayos[server]
relayos serve --open
```

---

## 🌐 语言

- [English](README.md)
- [Deutsch (German)](README_DE.md)
- [Français (French)](README_FR.md)
- [Español (Spanish)](README_ES.md)
- [日本語 (Japanese)](README_JP.md)
- [한국어 (Korean)](README_KR.md)

---

## 📄 许可证

[Apache 2.0](LICENSE) Copyright 2026 [jjjjjjjjnnjnn](https://github.com/jjjjjjjjnnjnn)

---

<p align="center">
  <strong>别再在 AI 工具之间复制粘贴了。<br>
  Fork、merge、串联你的对话。</strong><br>
  <br>
  <a href="https://github.com/jjjjjjjjnnjnn/relayos"><img src="https://img.shields.io/badge/GitHub-★-181717?style=for-the-badge&logo=github" alt="GitHub"></a>
  <a href="#-快速开始"><img src="https://img.shields.io/badge/开始使用-10B981?style=for-the-badge" alt="开始使用"></a>
  <br>
  <sub><code>pip install relayos && relay</code></sub>
</p>
