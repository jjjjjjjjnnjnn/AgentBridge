# RelayOS V2: Agent Operating System — 架构计划

## 核心升级

从"多模型路由工具"升级为"终端原生的 Agent Operating System"。

---

## 一、核心实体

### 1. Project（项目）
- 保存 Conversations、Workers、Knowledge、Models
- 跨对话共享记忆

### 2. Conversation（对话）
- 升级自 Session
- 每个 Conversation 属于一个 Project
- 有标题、参与者、上下文

### 3. Integrated Conversation（集成对话） ⭐ 核心创新
- 把 N 个已有对话合并为一个新对话
- 形成 Conversation Graph
- 例如：#12 数据库设计 + #18 缓存方案 → #31 系统架构

### 4. Worker（工作者）
- 不是模型，是角色
- Architect / Coder / Researcher / Reviewer / Debugger
- 模型只是 backend 实现

### 5. Knowledge（知识）
- 项目的长期记忆
- 提取自 Conversation Artifacts
- 纯代码提取，零 LLM

---

## 二、TUI 布局

```
┌────────────┬─────────────────────────────────┬─────────────┐
│  Navigation │         Workspace              │   Context   │
├────────────┼─────────────────────────────────┼─────────────┤
│ [N] New    │  ┌─────────────────────────┐    │ Project     │
│ [R] Recent │  │ User: 设计支付系统       │    │   relayos   │
│ [I] Integr │  │                         │    │             │
│ [G] Graph  │  │ Architect: ...          │    │ Workers     │
│ [K] Knowl  │  │ Coder: ...              │    │   [A] Arch  │
│ [W] Worker │  │ Researcher: ...         │    │   [C] Coder │
│ [P] Proj   │  └─────────────────────────┘    │             │
│ [?] Help   │                                  │ Budget     │
│             │                                  │   $0.32    │
│ #42 Payment│                                  │ Profile    │
│ #41 Auth   │                                  │   Balanced │
│ #40 API    │                                  │ Memory     │
│             │                                  │   32 items │
└────────────┴──────────────────────────────────┴─────────────┘
```

---

## 三、TUI 键盘布局

| 按键 | 功能 |
|------|------|
| `q` | 退出 |
| `n` | New Conversation |
| `r` | Recent Conversations |
| `i` | Integrate Conversations |
| `g` | Conversation Graph |
| `k` | Knowledge view |
| `w` | Workers view |
| `p` | Project settings |
| `s` | Settings |
| `?` | Help |
| `1-9` | Select conversation |
| `a` | Architect worker |
| `c` | Coder worker |
| `v` | Reviewer worker |
| `d` | Debugger worker |

### 聊天内命令

| 命令 | 功能 |
|------|------|
| `/new` | 新对话（在当前项目内）|
| `/fork` | 从当前对话分叉 |
| `/merge 1 2 3` | 把多个对话合并为集成对话 |
| `/attach 42` | 把对话#42 加入当前上下文 |
| `/summarize` | 总结当前对话 |
| `/export` | 导出对话 |
| `/knowledge` | 保存为知识 |
| `/group` | 多 Worker 讨论 |

---

## 四、实施阶段

### Phase 1 — Project + Conversation 系统
- [ ] Project 存储（升级自 project store）
- [ ] Conversation 存储（升级自 session store）
- [ ] Integrated Conversation 创建流程
- [ ] Conversation Graph 数据模型

### Phase 2 — TUI 重写
- [ ] 三栏布局（Nav | Chat | Context）
- [ ] 左侧 Conversations 列表
- [ ] 中间 Chat Area
- [ ] 右侧 Context Panel
- [ ] 欢迎页

### Phase 3 — 键盘命令
- [ ] 单键命令系统（n, r, i, g, k, w, p, s, ?）
- [ ] / 命令系统（/new, /fork, /merge, /attach）
- [ ] ? 帮助页
- [ ] Worker 快捷选择（a, c, v, d）

### Phase 4 — Conversation Graph
- [ ] Graph 数据结构和存储
- [ ] Graph 可视化（TUI）
- [ ] Integrated Conversation 创建流程
- [ ] Merge / Fork / Attach 实现

### Phase 5 — 知识系统增强
- [ ] Knowledge 在 TUI 中展示
- [ ] 从 Conversation 提取知识
- [ ] 知识搜索
