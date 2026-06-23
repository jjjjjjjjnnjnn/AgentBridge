<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/RelayOS-v0.1.0a1-8B5CF6?style=for-the-badge" alt="RelayOS">
  </picture>
</p>

<h1 align="center">RelayOS</h1>

<p align="center">
  <strong>AI 도구 간 복사-붙여넣기는 이제 그만.</strong><br>
  Claude, GPT, Gemini, DeepSeek 및 로컬 모델 전반에 걸쳐<br>
  공유 메모리, 워크플로 오케스트레이션, MCP 통합을 갖춘<br>
  영구적인 AI 워커를 생성하세요.
</p>

<p align="center">
  <a href="#-빠른-시작"><img src="https://img.shields.io/badge/-빠른_시작-10B981?style=flat-square" alt="빠른 시작"></a>
  <a href="#-기능"><img src="https://img.shields.io/badge/-기능-3B82F6?style=flat-square" alt="기능"></a>
  <a href="#%EF%B8%8F-설정"><img src="https://img.shields.io/badge/-설정-8B5CF6?style=flat-square" alt="설정"></a>
  <a href="#-예제"><img src="https://img.shields.io/badge/-예제-F59E0B?style=flat-square" alt="예제"></a>
  <a href="#%EF%B8%8F-아키텍처"><img src="https://img.shields.io/badge/-아키텍처-EC4899?style=flat-square" alt="아키텍처"></a>
  <a href="#%EF%B8%8F-감사의-말"><img src="https://img.shields.io/badge/-감사의_말-6366F1?style=flat-square" alt="감사의 말"></a>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文-文档-EA4335?style=flat-square" alt="中文"></a>
  <a href="README_DE.md"><img src="https://img.shields.io/badge/Deutsch-Dokument-FFD700?style=flat-square" alt="Deutsch"></a>
  <a href="README_ES.md"><img src="https://img.shields.io/badge/Español-Doc-00C853?style=flat-square" alt="Español"></a>
  <a href="README_FR.md"><img src="https://img.shields.io/badge/Français-Doc-1E90FF?style=flat-square" alt="Français"></a>
  <a href="README_JP.md"><img src="https://img.shields.io/badge/日本語-ドキュメント-FF4081?style=flat-square" alt="日本語"></a>
  <a href="README_KR.md"><img src="https://img.shields.io/badge/한국어-문서-03C75A?style=flat-square" alt="한국어"></a>
</p>

---

## 📋 목차

| 섹션 | 설명 |
|---------|-------------|
| [🎯 개요](#-개요) | RelayOS가 무엇이고 왜 필요한지 |
| [✨ 기능](#-기능) | 현재 기능 |
| [⚡ 빠른 시작](#-빠른-시작) | 설치 및 첫 워크플로 실행 |
| [📖 사용자 가이드](#-사용자-가이드) | 워크플로, 터미널, 메모리 |
| [⚙️ 설정](#%EF%B8%8F-설정) | 프로바이더, 터미널, 라우팅 |
| [🏗️ 아키텍처](#%EF%B8%8F-아키텍처) | 시스템 설계 |
| [📁 예제](#-예제) | 즉시 사용 가능한 워크플로 |
| [🛣️ 로드맵](#%EF%B8%8F-로드맵) | 향후 계획 |
| [🙏 감사의 말](#%EF%B8%8F-감사의-말) | 감사의 말 |
| [📄 라이선스](#-라이선스) | Apache 2.0 |

---

## 🎯 개요

**RelayOS**는 AI 에이전트를 위한 오픈소스 조정 레이어입니다——Docker가 컨테이너를 위한 것처럼, AI 도구를 위한 것입니다.

### 문제

여러분은 **Claude Code**를 아키텍처에, **ChatGPT**를 추론에, **Gemini**를 연구에, **DeepSeek**를 코딩에 사용합니다. 각 도구는 훌륭하지만, **서로 대화하지 않습니다.** 시간의 30%를 도구 간 컨텍스트 복사-붙여넣기와 무료 모델로 처리할 수 있는 작업에 프리미엄 토큰을 소모하는 데 낭비하고 있습니다.

### 해결책

```
┌─────────────────────────────────────────────────────┐
│                    AI 도구                             │
│   Claude Code    ChatGPT    Gemini    DeepSeek       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   RelayOS                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  터미널 풀  │  │ 워크플로    │  │  공유 메모리  │  │
│  │ (멀티 CLI)  │  │ 엔진(YAML) │  │  (SQLite)   │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │  어댑터     │  │ MCP 클라이언트│                  │
│  │ (5 프로바이더)│  │  (도구)    │                    │
│  └─────────────┘  └─────────────┘                    │
└──────────────────────────────────────────────────────┘
```

---

## ✨ 기능

### 🤖 멀티 터미널 풀
- 동일한 CLI 도구의 **여러 인스턴스**를 동시에 실행 (예: 3개의 Claude Code 터미널)
- 각 터미널은 **독립적인 모델 선택** 가능
- 세션 간 **영구 유지** (SQLite 기반)

**지원 터미널:** `claude`, `mimo`, `opencode`, `codex`, `qcode`, `custom`

### 🔄 워크플로 엔진
- **순차** 파이프라인——단계 간 템플릿 변수 해석 지원
- 여러 터미널에서 동시 **병렬** 실행
- YAML 정의 워크플로——코딩 불필요

### 🧠 공유 메모리
- **에이전트 간 컨텍스트**: 각 에이전트는 이전 에이전트의 출력을 참조 가능
- **SQLite 영속성**: 메모리가 세션을 넘어 유지됨
- **명명된 키**: `save_as`를 통한 의미적 참조

### 🔗 MCP 통합
- **모든 MCP 서버**에 연결하여 도구 사용
- Stdio 기반 MCP 클라이언트, 타임아웃 및 오류 처리 지원

### 💰 비용 인식 라우팅 (계획 중)
- 무료 모델 우선, 필요할 때만 유료 모델 사용
- 정책별 라우팅 (품질 우선 vs 속도 우선 vs 비용 우선)

---

## ⚡ 빠른 시작

### 설치

```bash
pip install relayos
```

### 초기화

```bash
relayos init
```

환경 변수를 통해 API 키를 설정하세요:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export DEEPSEEK_API_KEY="sk-..."
```

### 첫 번째 워크플로 실행

`hello.yaml` 파일을 생성하세요:

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

실행:

```bash
relayos run hello.yaml
```

### 터미널 관리

```bash
# 사용 가능한 터미널 유형 확인
relayos terminal types

# 아키텍처용 Claude Code 터미널 생성
relayos terminal create claude -n architect -m claude-sonnet-4-20250514

# 빠른 작업용 터미널 추가 생성
relayos terminal create claude -n assistant -m claude-haiku-4-20251001

# 연구용 Gemini 터미널 생성
relayos terminal create google -n researcher -m gemini-2.5-flash

# 실행 중인 모든 터미널 보기
relayos terminal list

# 특정 터미널에서 프롬프트 실행
relayos terminal exec opencode "Analyze this data"
```

---

## 📖 사용자 가이드

### 워크플로

워크플로는 멀티 에이전트 파이프라인을 정의하는 YAML 파일입니다:

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

| 필드 | 설명 |
|-------|-------------|
| `agent` | 사용할 터미널 유형 (anthropic, google, openai, opencode, deepseek) |
| `prompt` | 보낼 프롬프트 |
| `save_as` | 공유 메모리에 결과를 저장할 키 이름 |
| `system` | 시스템 프롬프트 (선택 사항) |
| `model` | 모델 재정의 (선택 사항) |
| `parallel` | `true`로 설정하면 병렬 그룹에서 실행 |

### 터미널

RelayOS는 각 AI CLI를 "터미널"——독립적으로 실행되는 워커로 취급합니다:

| 터미널 | 바이너리 | 기본 모델 | 상태 |
|----------|--------|---------------|--------|
| `claude` | `claude` | claude-sonnet-4-20250514 | ✅ 사용 가능 |
| `mimo` | `mimo` | gpt-4o | ✅ 사용 가능 |
| `opencode` | `opencode` | deepseek-chat | ✅ 사용 가능 |
| `codex` | `codex` | gpt-4o | ❌ 설치되지 않음 |
| `qcode` | `q` | qwen2.5:7b | ❌ 설치되지 않음 |
| `custom` | (설정 가능) | 사용자 정의 | ⚡ 사용자 정의 |

### 공유 메모리

```bash
# 저장
relayos remember my_key "some value"

# 검색
relayos recall my_key

# 모든 키 나열
relayos memory-list
```

---

## ⚙️ 설정

설정 파일 위치: `~/.relayos/config.yaml` (또는 `$RELAYOS_CONFIG_DIR/config.yaml`)

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

**API 키 우선순위:**
1. 설정 파일의 `api_key` 필드
2. 환경 변수 (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY` 등)
3. 비어 있음 (어댑터가 경고 표시)

---

## 🏗️ 아키텍처

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
                    │  │  터미널 풀     │──│──→ Claude Code, Mimo, OpenCode...
                    │  │  (멀티 인스턴스)│  │
                    │  ├────────────────┤  │
                    │  │ 워크플로 엔진  │  │
                    │  │ (YAML 파서)    │  │
                    │  ├────────────────┤  │
                    │  │   스케줄러     │──│──→ 순차 / 병렬
                    │  ├────────────────┤  │
                    │  │   공유 메모리   │  │
                    │  │   (SQLite)     │  │
                    │  ├────────────────┤  │
                    │  │    어댑터      │──│──→ OpenAI / Claude / Gemini...
                    │  ├────────────────┤  │
                    │  │ MCP 클라이언트  │──│──→ GitHub MCP / Filesystem MCP...
                    │  └────────────────┘  │
                    └──────────────────────┘
```

### 설계 결정

| 결정 | 선택 | 이유 |
|----------|--------|-----------|
| CLI 우선 | Click + YAML | 코드 없는 워크플로; 비개발자도 파이프라인 생성 가능 |
| 멀티 인스턴스 | 스레드 풀 | 여러 모델에서 동시에 에이전트 실행 |
| 영속성 | SQLite | 외부 종속성 없는 세션 간 메모리 |
| 어댑터 | httpx 기반 | 최소 종속성; 프로바이더 SDK 불필요 |
| MCP | 클라이언트 전용 (v0.1) | MCP 서버 활용; v1.0에서 Hub 모드 |

---

## 📁 예제

| 예제 | 설명 |
|---------|-------------|
| `examples/saas-builder.yaml` | 4-에이전트 SaaS 설계 파이프라인: Gemini 연구 → Claude 설계 → GPT 코딩 → DeepSeek 검토 |
| `examples/linguagraph-research.yaml` | 3-에이전트 연구 파이프라인: 언어 분석 → 인지 모델 → 논문 작성 |
| `examples/debate.yaml` | 3-에이전트 토론: 로컬 vs 클라우드 LLM, Gemini가 평가 |
| `examples/parallel-research.yaml` | 종합 분석이 포함된 4-에이전트 병렬 연구 스프린트 |

---

## 🛣️ 로드맵

- **v0.1** — ✅ CLI, YAML 워크플로, 5개 어댑터, 공유 메모리, MCP 클라이언트, 터미널 풀
- **v0.2** — 🔄 웹 대시보드 (Next.js), 워크플로 시각화, 비용 인식 라우팅, Docker
- **v0.5** — 🔄 LangGraph 오케스트레이션, 조건부 분기, Human-in-the-loop
- **v1.0** — 🔄 양방향 MCP Hub, 플러그인 시스템, 벡터 메모리

---

## 🙏 감사의 말

RelayOS는 거인의 어깨 위에 서 있습니다. 다음 프로젝트에 깊은 감사를 드립니다:

### 🖥️ 터미널 플랫폼

| 플랫폼 | 감사의 말 |
|----------|--------|
| **[Claude Code](https://claude.ai)** — Anthropic 제공 | 주요 개발 플랫폼. RelayOS는 Claude Code의 에이전트 오케스트레이션 기능을 사용하여 설계 및 구축되었습니다. [약관](https://www.anthropic.com/legal) · [개인정보](https://www.anthropic.com/privacy) |
| **[OpenCode](https://opencode.ai)** | 터미널 어댑터 대상 및 테스트 파트너. OpenCode CLI는 RelayOS의 터미널 풀이 사용하는 실행 인터페이스를 제공합니다. |
| **[MimoCode](https://mimo.ai)** | 터미널 어댑터 대상. Mimo의 CLI 통합은 멀티 모델 프론트엔드 워크플로를 가능하게 합니다. |
| **OpenAI Codex** | 코딩 작업을 위한 터미널 어댑터 대상. |

### 🤖 개발에 사용된 AI 모델

- **Claude Opus 4.8 / Sonnet 4.6** (Anthropic) — 주요 개발 모델
- **Gemini 2.5 Flash** (Google) — 연구 작업, 경쟁 분석
- **GPT-4o** (OpenAI) — 아키텍처 평가 및 검토
- **DeepSeek V3** (DeepSeek) — 코드 리뷰 및 테스트

### 📦 오픈소스 의존성

| 의존성 | 라이선스 | 용도 |
|------------|---------|---------|
| [Click](https://palletsprojects.com/p/click/) | BSD-3-Clause | CLI 프레임워크 |
| [PyYAML](https://pyyaml.org/) | MIT | YAML 파싱 |
| [HTTPX](https://www.python-httpx.org/) | BSD-3-Clause | 모델 API용 HTTP 클라이언트 |
| [pydantic](https://docs.pydantic.dev/) (계획 중) | MIT | 설정 검증 (v0.2) |

### 🧠 스킬 및 지식 출처

- **ECC (Engineering Claude Code)** 플러그인 시스템 — 에이전트 오케스트레이션 패턴
- **Claude Scholar** — 학술 연구 워크플로 패턴
- **MCP (Model Context Protocol)** — Anthropic의 도구 통합 프로토콜

### 🌍 커뮤니티 번역

RelayOS README는 다음 언어로 제공됩니다:
- [中文 (Chinese)](README_ZH.md)
- [Deutsch (German)](README_DE.md)
- [Français (French)](README_FR.md)
- [Español (Spanish)](README_ES.md)
- [日本語 (Japanese)](README_JP.md)
- [한국어 (Korean)](README_KR.md)

---

## 📄 라이선스

[Apache 2.0](LICENSE) Copyright 2026 [jjjjjjjjnnjnn](https://github.com/jjjjjjjjnnjnn)

---

<p align="center">
  <strong>RelayOS</strong> — AI 에이전트를 위한 조정 레이어.<br>
  <sub>오픈소스 AI 커뮤니티를 위해 ❤️를 담아</sub>
</p>
