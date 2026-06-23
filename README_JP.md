<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/RelayOS-v0.1.0a1-8B5CF6?style=for-the-badge" alt="RelayOS">
  </picture>
</p>

<h1 align="center">RelayOS</h1>

<p align="center">
  <strong>AIツール間のコピー＆ペーストとはもうおさらば。</strong><br>
  Claude、GPT、Gemini、DeepSeek、ローカルモデル間で永続的なAIワーカーを作成——<br>
  共有メモリ、ワークフローオーケストレーション、MCP統合を備えて。
</p>

<p align="center">
  <a href="#-クイックスタート"><img src="https://img.shields.io/badge/-クイックスタート-10B981?style=flat-square" alt="クイックスタート"></a>
  <a href="#-機能"><img src="https://img.shields.io/badge/-機能-3B82F6?style=flat-square" alt="機能"></a>
  <a href="#%EF%B8%8F-設定"><img src="https://img.shields.io/badge/-設定-8B5CF6?style=flat-square" alt="設定"></a>
  <a href="#-例"><img src="https://img.shields.io/badge/-例-F59E0B?style=flat-square" alt="例"></a>
  <a href="#%EF%B8%8F-アーキテクチャ"><img src="https://img.shields.io/badge/-アーキテクチャ-EC4899?style=flat-square" alt="アーキテクチャ"></a>
  <a href="#%EF%B8%8F-謝辞"><img src="https://img.shields.io/badge/-謝辞-6366F1?style=flat-square" alt="謝辞"></a>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文-文档-EA4335?style=flat-square" alt="中文"></a>
  <a href="README_DE.md"><img src="https://img.shields.io/badge/Deutsch-Dokument-FFD700?style=flat-square" alt="Deutsch"></a>
  <a href="README_ES.md"><img src="https://img.shields.io/badge/Español-Doc-00C853?style=flat-square" alt="Español"></a>
  <a href="README_FR.md"><img src="https://img.shields.io/badge/Français-Doc-1E90FF?style=flat-square" alt="Français"></a>
  <a href="README_JP.md"><img src="https://img.shields.io/badge/日本語-ドキュメント-FF4081?style=flat-square" alt="日本語"></a>
  <a href="README_KR.md"><img src="https://img.shields.io/badge/한국어-문서-03C75A?style=flat-square" alt="한국어"></a>
</p>

---

## 📋 目次

| セクション | 説明 |
|---------|-------------|
| [🎯 概要](#-概要) | RelayOSの概要と存在理由 |
| [✨ 機能](#-機能) | 現在の機能 |
| [⚡ クイックスタート](#-クイックスタート) | インストールと最初のワークフロー |
| [📖 ユーザーガイド](#-ユーザーガイド) | ワークフロー、ターミナル、メモリ |
| [⚙️ 設定](#%EF%B8%8F-設定) | プロバイダ、ターミナル、ルーティング |
| [🏗️ アーキテクチャ](#%EF%B8%8F-アーキテクチャ) | システム設計 |
| [📁 例](#-例) | すぐ使えるワークフロー |
| [🛣️ ロードマップ](#%EF%B8%8F-ロードマップ) | 将来計画 |
| [🙏 謝辞](#%EF%B8%8F-謝辞) | 謝辞 |
| [📄 ライセンス](#-ライセンス) | Apache 2.0 |

---

## 🎯 概要

**RelayOS** はAIエージェントのためのオープンソースの協調レイヤーです——Dockerがコンテナに対してそうであるように、AIツールのためのものです。

### 問題

あなたは **Claude Code** をアーキテクチャに、**ChatGPT** を推論に、**Gemini** を調査に、**DeepSeek** をコーディングに使っています。各ツールは優れていますが、**それらは互いに通信しません。** 時間の30%をツール間のコンテキストのコピー＆ペーストや、無料モデルで十分なタスクにプレミアムトークンを浪費することに費やしています。

### 解決策

```
┌─────────────────────────────────────────────────────┐
│                    AIツール                            │
│   Claude Code    ChatGPT    Gemini    DeepSeek       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   RelayOS                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  ターミナル  │  │ ワークフロー │  │  共有メモリ  │  │
│  │  プール     │  │  エンジン   │  │  (SQLite)   │  │
│  │ (マルチCLI) │  │  (YAML)     │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │  アダプター  │  │ MCPクライアント│                  │
│  │ (5 プロバイダ)│  │  (ツール)   │                    │
│  └─────────────┘  └─────────────┘                    │
└──────────────────────────────────────────────────────┘
```

---

## ✨ 機能

### 🤖 マルチターミナルプール
- 同じCLIツールの**複数インスタンス**を同時実行（例：3つのClaude Codeターミナル）
- 各ターミナルは**独立したモデル選択**が可能
- セッション間で**永続化**（SQLiteベース）

**対応ターミナル：** `claude`、`mimo`、`opencode`、`codex`、`qcode`、`custom`

### 🔄 ワークフローエンジン
- **順次**パイプライン——ステップ間のテンプレート変数解決対応
- **並列**実行——複数ターミナルで同時実行
- YAML定義のワークフロー——コーディング不要

### 🧠 共有メモリ
- **エージェント間コンテキスト**：各エージェントは前のエージェントの出力を参照可能
- **SQLite永続化**：メモリはセッションを超えて保持
- **名前付きキー**：`save_as` による意味的な参照

### 🔗 MCP統合
- **任意のMCPサーバー**に接続してツールを利用
- StdioベースのMCPクライアント、タイムアウトとエラー処理対応

### 💰 コスト認識ルーティング（計画中）
- 無料モデルを優先、必要な場合のみ有料モデル
- ポリシー別ルーティング（品質優先 vs 速度優先 vs コスト優先）

---

## ⚡ クイックスタート

### インストール

```bash
pip install relayos
```

### 初期化

```bash
relayos init
```

環境変数でAPIキーを設定：

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export DEEPSEEK_API_KEY="sk-..."
```

### 最初のワークフローを実行

`hello.yaml` ファイルを作成：

```yaml
name: "Hello Multi-Agent"

steps:
  - agent: google
    prompt: "List 3 interesting facts about the MCP protocol."
    save_as: research

  - agent: anthropic
    prompt: "Based on: {{research}}\nDesign a simple architecture."
    save_as: architecture
```

実行：

```bash
relayos run hello.yaml
```

### ターミナルの管理

```bash
# 利用可能なターミナルタイプを確認
relayos terminal types

# アーキテクチャ用のClaude Codeターミナルを作成
relayos terminal create claude -n architect -m claude-sonnet-4-20250514

# クイックタスク用にもう一つ作成
relayos terminal create claude -n assistant -m claude-haiku-4-20251001

# 調査用のGeminiターミナルを作成
relayos terminal create google -n researcher -m gemini-2.5-flash

# 実行中の全ターミナルを表示
relayos terminal list

# 特定のターミナルでプロンプトを実行
relayos terminal exec opencode "Analyze this data"
```

---

## 📖 ユーザーガイド

### ワークフロー

ワークフローはマルチエージェントパイプラインを定義するYAMLファイルです：

```yaml
name: "Pipeline Name"
description: "What this pipeline does"

vars:
  topic: "AI safety"

steps:
  - agent: google
    prompt: "Research {{topic}}"
    save_as: research
    system: "You are a research analyst."

  - agent: anthropic
    prompt: "Design based on: {{research}}"
    save_as: design
```

| フィールド | 説明 |
|-------|-------------|
| `agent` | 使用するターミナルタイプ（claude、gemini、gpt、opencode、deepseek） |
| `prompt` | 送信するプロンプト |
| `save_as` | 共有メモリに結果を保存するキー名 |
| `system` | システムプロンプト（オプション） |
| `model` | モデルの上書き（オプション） |
| `parallel` | `true` に設定すると並列グループで実行 |

### ターミナル

RelayOSは各AI CLIを「ターミナル」——独立して動作するワーカーとして扱います：

| ターミナル | バイナリ | デフォルトモデル | ステータス |
|----------|--------|---------------|--------|
| `claude` | `claude` | claude-sonnet-4-20250514 | ✅ 利用可能 |
| `mimo` | `mimo` | gpt-4o | ✅ 利用可能 |
| `opencode` | `opencode` | deepseek-chat | ✅ 利用可能 |
| `codex` | `codex` | gpt-4o | ❌ 未インストール |
| `qcode` | `q` | qwen2.5:7b | ❌ 未インストール |
| `custom` | (設定可能) | ユーザー定義 | ⚡ カスタム |

### 共有メモリ

```bash
# 保存
relayos remember my_key "some value"

# 取得
relayos recall my_key

# 全キーを一覧表示
relayos memory-list
```

---

## ⚙️ 設定

設定ファイルの場所：`~/.relayos/config.yaml`（または `$RELAYOS_CONFIG_DIR/config.yaml`）

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

**APIキーの優先順位：**
1. 設定ファイルの `api_key` フィールド
2. 環境変数（`OPENAI_API_KEY`、`ANTHROPIC_API_KEY` など）
3. 空（アダプターが警告を表示）

---

## 🏗️ アーキテクチャ

```
                    ┌─────────────────────┐
                    │   CLI (Click)       │
                    │  relayos run     │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   RelayOS Core    │
                    │                      │
                    │  ┌────────────────┐  │
                    │  │  ターミナル    │──│──→ Claude Code, Mimo, OpenCode...
                    │  │  プール       │  │
                    │  │  (マルチインス)│  │
                    │  ├────────────────┤  │
                    │  │ ワークフロー   │  │
                    │  │ エンジン       │  │
                    │  │ (YAMLパーサー) │  │
                    │  ├────────────────┤  │
                    │  │  スケジューラ  │──│──→ 順次 / 並列
                    │  ├────────────────┤  │
                    │  │  共有メモリ    │  │
                    │  │  (SQLite)      │  │
                    │  ├────────────────┤  │
                    │  │   アダプター    │──│──→ OpenAI / Claude / Gemini...
                    │  ├────────────────┤  │
                    │  │ MCPクライアント │──│──→ GitHub MCP / Filesystem MCP...
                    │  └────────────────┘  │
                    └──────────────────────┘
```

### 設計上の決定

| 決定 | 選択 | 理由 |
|----------|--------|-----------|
| CLI優先 | Click + YAML | コード不要のワークフロー；非開発者でもパイプラインを作成可能 |
| マルチインスタンス | スレッドプール | 異なるモデルで同時にエージェントを実行 |
| 永続化 | SQLite | 外部依存なしのセッション間メモリ |
| アダプター | httpxベース | 最小限の依存関係；プロバイダSDK不要 |
| MCP | クライアントのみ（v0.1） | MCPサーバーを利用；v1.0でHubモード |

---

## 📁 例

| 例 | 説明 |
|---------|-------------|
| `examples/saas-builder.yaml` | 4エージェントSaaS設計パイプライン：Gemini調査 → Claude設計 → GPTコード → DeepSeekレビュー |
| `examples/linguagraph-research.yaml` | 3エージェント研究パイプライン：言語分析 → 認知モデル → 論文執筆 |
| `examples/debate.yaml` | 3エージェント討論：ローカル vs クラウドLLM、Geminiが判定 |
| `examples/parallel-research.yaml` | 4エージェント並列調査スプリント（統合あり） |

---

## 🛣️ ロードマップ

- **v0.1** — ✅ CLI、YAMLワークフロー、5アダプター、共有メモリ、MCPクライアント、ターミナルプール
- **v0.2** — 🔄 Webダッシュボード（Next.js）、ワークフロー可視化、コスト認識ルーティング、Docker
- **v0.5** — 🔄 LangGraphオーケストレーション、条件分岐、Human-in-the-loop
- **v1.0** — 🔄 双方向MCP Hub、プラグインシステム、ベクターメモリ

---

## 🙏 謝辞

RelayOSは巨人の肩の上に成り立っています。以下のプロジェクトに深く感謝いたします：

### 🖥️ ターミナルプラットフォーム

| プラットフォーム | 謝辞 |
|----------|--------|
| **[Claude Code](https://claude.ai)** — Anthropic提供 | 主要開発プラットフォーム。RelayOSはClaude Codeのエージェントオーケストレーション機能を使用して設計・構築されました。[利用規約](https://www.anthropic.com/legal) · [プライバシー](https://www.anthropic.com/privacy) |
| **[OpenCode](https://opencode.ai)** | ターミナルアダプター対象およびテストパートナー。OpenCode CLIはRelayOSのターミナルプールが使用する実行インターフェースを提供します。 |
| **[MimoCode](https://mimo.ai)** | ターミナルアダプター対象。MimoのCLI統合により、マルチモデルのフロントエンドワークフローが可能になります。 |
| **OpenAI Codex** | コーディングタスク向けターミナルアダプター対象。 |

### 🤖 開発に使用したAIモデル

- **Claude Opus 4.8 / Sonnet 4.6**（Anthropic）— 主要開発モデル
- **Gemini 2.5 Flash**（Google）— 調査タスク、競合分析
- **GPT-4o**（OpenAI）— アーキテクチャ評価とレビュー
- **DeepSeek V3**（DeepSeek）— コードレビューとテスト

### 📦 オープンソース依存関係

| 依存関係 | ライセンス | 目的 |
|------------|---------|---------|
| [Click](https://palletsprojects.com/p/click/) | BSD-3-Clause | CLIフレームワーク |
| [PyYAML](https://pyyaml.org/) | MIT | YAML解析 |
| [HTTPX](https://www.python-httpx.org/) | BSD-3-Clause | モデルAPI用HTTPクライアント |
| [pydantic](https://docs.pydantic.dev/)（計画中） | MIT | 設定検証（v0.2） |

### 🧠 スキルと知識ソース

- **ECC（Engineering Claude Code）** プラグインシステム — エージェントオーケストレーションパターン
- **Claude Scholar** — 学術研究ワークフローパターン
- **MCP（Model Context Protocol）** — Anthropicのツール統合プロトコル

### 🌍 コミュニティ翻訳

RelayOS READMEは以下の言語で利用可能です：
- [中文 (Chinese)](README_ZH.md)
- [Deutsch (German)](README_DE.md)
- [Français (French)](README_FR.md)
- [Español (Spanish)](README_ES.md)
- [日本語 (Japanese)](README_JP.md)
- [한국어 (Korean)](README_KR.md)

---

## 📄 ライセンス

[Apache 2.0](LICENSE) Copyright 2026 [jjjjjjjjnnjnn](https://github.com/jjjjjjjjnnjnn)

---

<p align="center">
  <strong>RelayOS</strong> — AIエージェントのための協調レイヤー。<br>
  <sub>オープンソースAIコミュニティのために ❤️ を込めて</sub>
</p>
