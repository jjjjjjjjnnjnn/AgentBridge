# RelayOS Demo GIF Script

## 总览

一个 30 秒的终端录屏，展示 RelayOS 的核心差异化：
**Git for AI Conversations — /fork → /merge → /graph**

没有文案介绍，没有复杂概念。用户看到的就是操作本身。

---

## 分镜

### Frame 1: 问题（3 秒）

```
$ relay "设计支付系统"

┌─ RelayOS  [AUTO]  $0 ─────────────────────┐
│                                             │
│  > 设计支付系统                               │
│                                             │
│  [architect] 建议使用事件溯源架构             │
│    1. 幂等性天然保证                         │
│    2. 审计日志免费获得                       │
│                                             │
│  [reviewer] 发现 2 个安全问题               │
│    JWT 未设置过期时间                        │
│    缺少速率限制                             │
│                                             │
├─────────────────────────────────────────────┤
│ >                                            │
└─────────────────────────────────────────────┘
```

### Frame 2: /fork（5 秒）

输入 `/fork stripe`：

```
> /fork stripe

┌─ RelayOS  sess-31  [AUTO]  $0 ─────────────┐
│                                             │
│  ✓ Forked → sess-3a (from sess-31)         │
│                                             │
│  [architect] 事件溯源方案...                 │
│                                             │
│                                             │
├─────────────────────────────────────────────┤
│ > /fork stripe█                               │
└─────────────────────────────────────────────┘
```

### Frame 3: 再 /fork（5 秒）

```
> /fork crypto

┌─ RelayOS  sess-3b  [AUTO]  $0 ─────────────┐
│                                             │
│  ✓ Forked → sess-3b (from sess-31)         │
│                                             │
│  [architect] 加密支付方案...                 │
│                                             │
│                                             │
├─────────────────────────────────────────────┤
│ > /fork crypto█                               │
└─────────────────────────────────────────────┘
```

### Frame 4: /merge（5 秒）

```
> /merge sess-3a sess-3b

┌─ RelayOS  sess-3c  Derived: #3a #3b  [AUTO] ┐
│                                               │
│  ✓ Merged 2 sessions → sess-3c              │
│                                               │
│  [architect] 综合两种方案，推荐...            │
│    混合架构：核心用事件溯源                   │
│    支付通道用加密方案                         │
│                                               │
├───────────────────────────────────────────────┤
│ > █                                            │
└───────────────────────────────────────────────┘
```

### Frame 5: Ctrl+G 对话图（5 秒）

```
> Ctrl+G

┌─ RelayOS  Conversation Graph ──────────────┐
│                                             │
│  └── 支付系统设计 [sess-31]                 │
│       ├── /fork → Stripe 方案 [sess-3a]     │
│       │                                      │
│       ├── /fork → Crypto 方案 [sess-3b]     │
│       │                                      │
│       └── /merge → 最终架构 [sess-3c] ▶    │
│               ▲                              │
│               │                              │
│  /fork /merge │ 3 branches, 1 result         │
│                                             │
├─────────────────────────────────────────────┤
│  Esc=close  j/k=navigate                     │
└─────────────────────────────────────────────┘
```

### Frame 6: 回到对话（3 秒）

```
> Esc

┌─ RelayOS  sess-3c  Derived: #3a #3b  [AUTO] ┐
│                                               │
│  [architect] 最终架构方案：                    │
│    API Gateway → Event Store → Payment        │
│    Webhook → Notification                     │
│                                               │
│  ✓ Stripe + Crypto 方案整合完成               │
│                                               │
├───────────────────────────────────────────────┤
│ > █                                            │
└───────────────────────────────────────────────┘
```

---

## 技术实现

### 工具选择

推荐使用 **VHS**（https://github.com/charmbracelet/vhs）：

```bash
# 安装
go install github.com/charmbracelet/vhs@latest

# 编写 .tape 文件
vim demo.tape
```

### VHS Tape 文件

```tape
# relayos-demo.tape
Output relayos-demo.gif
Set FontSize 16
Set Width 900
Set Height 600

# Frame 1: 打开 RelayOS
Type "relay "支付系统设计""
Sleep 1s
Type "设计一个完整的支付系统"
Enter
Sleep 3s

# Frame 2: /fork
Type "/fork stripe"
Sleep 500ms
Enter
Sleep 3s

# Frame 3: 另一个 /fork
Type "/fork crypto"  
Sleep 500ms
Enter  
Sleep 3s

# Frame 4: /merge
Type "/merge sess-3a sess-3b"
Sleep 500ms
Enter
Sleep 3s

# Frame 5: 对话图
Ctrl+g
Sleep 2s

# Frame 6: 退出图
Esc
Sleep 2s
```

### 手动录制（备选）

如果没有 Go 环境，可以用 OBS + 终端录制：

```bash
# 1. 开一个终端，最大化
# 2. 运行 relay
# 3. 按顺序执行上面步骤
# 4. OBS 录制终端窗口
# 5. 剪辑为 30 秒 GIF
```

---

## GIF 在 README 中的位置

放在 README 第一屏，标题正下方：

```markdown
<p align="center">
  <strong>Git for AI Conversations</strong>
</p>

<p align="center">
  <img src="docs/demo.gif" alt="RelayOS Demo" width="800">
</p>

<p align="center">
  <code>pip install relayos && relay</code>
</p>
```

不再需要任何文案解释。用户看 GIF 就懂了。

---

## 成功标准

这个 GIF 应该让用户在 10 秒内理解三个问题：

1. **这是什么？** — 一个终端 AI 工作台
2. **能干什么？** — fork/merge 对话，形成关系图
3. **和 Claude Code 有什么区别？** — 不是 chat，是 conversation graph

如果用户看完 GIF 的第一反应是 "原来对话也可以 fork/merge"，定位就成功了。
