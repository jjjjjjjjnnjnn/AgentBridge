<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/AgentBridge-v0.1.0a1-8B5CF6?style=for-the-badge" alt="AgentBridge">
  </picture>
</p>

<h1 align="center">AgentBridge</h1>

<p align="center">
  <strong>Schluss mit Kopieren-und-Einfügen zwischen AI-Tools.</strong><br>
  Erstelle persistente KI-Arbeiter in Claude, GPT, Gemini, DeepSeek und lokalen Modellen —<br>
  mit gemeinsamem Speicher, Workflow-Orchestrierung und MCP-Integration.
</p>

<p align="center">
  <a href="#-schnellstart"><img src="https://img.shields.io/badge/-Schnellstart-10B981?style=flat-square" alt="Schnellstart"></a>
  <a href="#-funktionen"><img src="https://img.shields.io/badge/-Funktionen-3B82F6?style=flat-square" alt="Funktionen"></a>
  <a href="#%EF%B8%8F-konfiguration"><img src="https://img.shields.io/badge/-Konfiguration-8B5CF6?style=flat-square" alt="Konfiguration"></a>
  <a href="#-beispiele"><img src="https://img.shields.io/badge/-Beispiele-F59E0B?style=flat-square" alt="Beispiele"></a>
  <a href="#%EF%B8%8F-architektur"><img src="https://img.shields.io/badge/-Architektur-EC4899?style=flat-square" alt="Architektur"></a>
  <a href="#%EF%B8%8F-danksagungen"><img src="https://img.shields.io/badge/-Danksagungen-6366F1?style=flat-square" alt="Danksagungen"></a>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文-文档-EA4335?style=flat-square" alt="中文"></a>
  <a href="README_DE.md"><img src="https://img.shields.io/badge/Deutsch-Dokument-FFD700?style=flat-square" alt="Deutsch"></a>
  <a href="README_ES.md"><img src="https://img.shields.io/badge/Español-Doc-00C853?style=flat-square" alt="Español"></a>
  <a href="README_FR.md"><img src="https://img.shields.io/badge/Français-Doc-1E90FF?style=flat-square" alt="Français"></a>
  <a href="README_JP.md"><img src="https://img.shields.io/badge/日本語-ドキュメント-FF4081?style=flat-square" alt="日本語"></a>
  <a href="README_KR.md"><img src="https://img.shields.io/badge/한국어-문서-03C75A?style=flat-square" alt="한국어"></a>
</p>

---

## 📋 Inhaltsverzeichnis

| Abschnitt | Beschreibung |
|---------|-------------|
| [🎯 Übersicht](#-übersicht) | Was AgentBridge ist und warum es existiert |
| [✨ Funktionen](#-funktionen) | Aktuelle Fähigkeiten |
| [⚡ Schnellstart](#-schnellstart) | Installation und erster Workflow |
| [📖 Benutzerhandbuch](#-benutzerhandbuch) | Workflows, Terminals, Speicher |
| [⚙️ Konfiguration](#%EF%B8%8F-konfiguration) | Anbieter, Terminals, Routing |
| [🏗️ Architektur](#%EF%B8%8F-architektur) | Systemdesign |
| [📁 Beispiele](#-beispiele) | Fertige Workflows |
| [🛣️ Fahrplan](#%EF%B8%8F-fahrplan) | Zukunftspläne |
| [🙏 Danksagungen](#%EF%B8%8F-danksagungen) | Danksagungen |
| [📄 Lizenz](#-lizenz) | Apache 2.0 |

---

## 🎯 Übersicht

**AgentBridge** ist eine Open-Source-Koordinationsschicht für KI-Agenten — wie Docker für Container, aber für KI-Werkzeuge.

### Das Problem

Du verwendest **Claude Code** für Architektur, **ChatGPT** für logisches Denken, **Gemini** für Recherche, **DeepSeek** zum Programmieren. Jedes Werkzeug ist exzellent. **Sie kommunizieren nicht miteinander.** Du verschwendest 30 % deiner Zeit damit, Kontext zwischen Tools zu kopieren und Premium-Token für Aufgaben zu verbrennen, die ein kostenloses Modell erledigen könnte.

### Die Lösung

```
┌─────────────────────────────────────────────────────┐
│                Deine AI-Tools                        │
│   Claude Code    ChatGPT    Gemini    DeepSeek       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   AgentBridge                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ Terminal-   │  │  Workflow-  │  │  Gemeinsamer │  │
│  │ Pool        │  │  Engine     │  │  Speicher    │  │
│  │ (Multi-CLI) │  │  (YAML)     │  │  (SQLite)    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │  Adapter    │  │ MCP-Client  │                    │
│  │ (5 Anbieter)│  │  (Tools)    │                    │
│  └─────────────┘  └─────────────┘                    │
└──────────────────────────────────────────────────────┘
```

---

## ✨ Funktionen

### 🤖 Multi-Terminal-Pool
- **Mehrere Instanzen** desselben CLI-Tools gleichzeitig ausführen (z. B. 3 Claude Code Terminals)
- Jedes Terminal hat eine **unabhängige Modellauswahl**
- **Persistent** über Sitzungen hinweg (SQLite-gestützt)

**Unterstützte Terminals:** `claude`, `mimo`, `opencode`, `codex`, `qcode`, `custom`

### 🔄 Workflow-Engine
- **Sequenzielle** Pipelines mit Template-Variablen-Auflösung zwischen Schritten
- **Parallele** Ausführung über mehrere Terminals gleichzeitig
- YAML-definierte Workflows — keine Programmierkenntnisse erforderlich

### 🧠 Gemeinsamer Speicher
- **Agentenübergreifender Kontext**: Jeder Agent sieht die Ausgabe vorheriger Agenten
- **SQLite-Persistenz**: Speicher überdauert Sitzungen
- **Benannte Schlüssel**: `save_as` für semantische Referenz

### 🔗 MCP-Integration
- Verbindung zu **beliebigen MCP-Servern** für Werkzeuge
- Stdio-basierter MCP-Client mit Timeout und Fehlerbehandlung

### 💰 Kostenbewusstes Routing (geplant)
- Kostenlose Modelle zuerst, kostenpflichtige nur bei Bedarf
- Richtlinienbasiertes Routing (Qualität vs. Geschwindigkeit vs. Kosten)

---

## ⚡ Schnellstart

### Installation

```bash
pip install agentbridge
```

### Initialisierung

```bash
agentbridge init
```

Konfiguriere deine API-Schlüssel über Umgebungsvariablen:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export DEEPSEEK_API_KEY="sk-..."
```

### Ausführen deines ersten Workflows

Erstelle eine Datei `hello.yaml`:

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

Führe sie aus:

```bash
agentbridge run hello.yaml
```

### Terminals verwalten

```bash
# Verfügbare Terminal-Typen anzeigen
agentbridge terminal types

# Ein Claude Code Terminal für Architektur erstellen
agentbridge terminal create claude -n architect -m claude-sonnet-4-20250514

# Ein weiteres für schnelle Aufgaben
agentbridge terminal create claude -n assistant -m claude-haiku-4-20251001

# Ein Gemini-Terminal für Recherche erstellen
agentbridge terminal create google -n researcher -m gemini-2.5-flash

# Alle laufenden Terminals anzeigen
agentbridge terminal list

# Einen Prompt auf einem bestimmten Terminal ausführen
agentbridge terminal exec opencode "Analyze this data"
```

---

## 📖 Benutzerhandbuch

### Workflows

Workflows sind YAML-Dateien, die Multi-Agent-Pipelines definieren:

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

| Feld | Beschreibung |
|-------|-------------|
| `agent` | Zu verwendender Terminal-Typ (claude, gemini, gpt, opencode, deepseek) |
| `prompt` | Der zu sendende Prompt |
| `save_as` | Schlüssel zur Speicherung des Ergebnisses im gemeinsamen Speicher |
| `system` | System-Prompt (optional) |
| `model` | Modellüberschreibung (optional) |
| `parallel` | Auf `true` setzen, um den Schritt in einer parallelen Gruppe auszuführen |

### Terminals

AgentBridge behandelt jedes AI-CLI als "Terminal" — einen unabhängig laufenden Arbeiter:

| Terminal | Binärdatei | Standard-Modell | Status |
|----------|--------|---------------|--------|
| `claude` | `claude` | claude-sonnet-4-20250514 | ✅ Verfügbar |
| `mimo` | `mimo` | gpt-4o | ✅ Verfügbar |
| `opencode` | `opencode` | deepseek-chat | ✅ Verfügbar |
| `codex` | `codex` | gpt-4o | ❌ Nicht installiert |
| `qcode` | `q` | qwen2.5:7b | ❌ Nicht installiert |
| `custom` | (konfigurierbar) | benutzerdefiniert | ⚡ Benutzerdefiniert |

### Gemeinsamer Speicher

```bash
# Speichern
agentbridge remember my_key "some value"

# Abrufen
agentbridge recall my_key

# Alle Schlüssel auflisten
agentbridge memory-list
```

---

## ⚙️ Konfiguration

Konfigurationsdatei-Pfad: `~/.agentbridge/config.yaml` (oder `$AGENTBRIDGE_CONFIG_DIR/config.yaml`)

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

**API-Schlüssel-Priorität:**
1. `api_key`-Feld in der Konfigurationsdatei
2. Umgebungsvariable (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, usw.)
3. Leer (Adapter gibt eine Warnung aus)

---

## 🏗️ Architektur

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
                    │  │  Terminal-Pool  │──│──→ Claude Code, Mimo, OpenCode...
                    │  │ (Multi-Inst.)   │  │
                    │  ├────────────────┤  │
                    │  │ Workflow-Engine │  │
                    │  │ (YAML-Parser)   │  │
                    │  ├────────────────┤  │
                    │  │   Scheduler     │──│──→ Sequenziell / Parallel
                    │  ├────────────────┤  │
                    │  │ Gemeinsamer     │  │
                    │  │ Speicher(SQLite)│  │
                    │  ├────────────────┤  │
                    │  │    Adapter      │──│──→ OpenAI / Claude / Gemini...
                    │  ├────────────────┤  │
                    │  │  MCP-Client     │──│──→ GitHub MCP / Filesystem MCP...
                    │  └────────────────┘  │
                    └──────────────────────┘
```

### Design-Entscheidungen

| Entscheidung | Wahl | Begründung |
|----------|--------|-----------|
| CLI-first | Click + YAML | Codefreie Workflows; auch Nicht-Entwickler können Pipelines erstellen |
| Multi-Instanz | Thread-Pool | Gleichzeitige Agenten auf verschiedenen Modellen ausführen |
| Persistenz | SQLite | Sitzungsübergreifender Speicher ohne externe Abhängigkeiten |
| Adapter | httpx-basiert | Minimale Abhängigkeiten; keine Anbieter-SDKs |
| MCP | Nur Client (v0.1) | MCP-Server nutzen; Hub-Modus in v1.0 |

---

## 📁 Beispiele

| Beispiel | Beschreibung |
|---------|-------------|
| `examples/saas-builder.yaml` | 4-Agent-SaaS-Design-Pipeline: Gemini Recherche → Claude Design → GPT Code → DeepSeek Review |
| `examples/linguagraph-research.yaml` | 3-Agent-Forschungspipeline: Sprachliche Analyse → Kognitives Modell → Paper-Schreiben |
| `examples/debate.yaml` | 3-Agent-Debatte: Pro-lokal vs. Pro-Cloud LLM, bewertet von Gemini |
| `examples/parallel-research.yaml` | 4-Agent-Parallel-Recherche-Sprint mit Synthese |

---

## 🛣️ Fahrplan

- **v0.1** — ✅ CLI, YAML-Workflows, 5 Adapter, gemeinsamer Speicher, MCP-Client, Terminal-Pool
- **v0.2** — 🔄 Web-Dashboard (Next.js), Workflow-Visualisierung, Kostenbewusstes Routing, Docker
- **v0.5** — 🔄 LangGraph-Orchestrierung, Bedingte Verzweigungen, Human-in-the-loop
- **v1.0** — 🔄 Bidirektionaler MCP-Hub, Plugin-System, Vektor-Speicher

---

## 🙏 Danksagungen

AgentBridge steht auf den Schultern von Giganten. Unser tiefster Dank gilt:

### 🖥️ Terminal-Plattformen

| Plattform | Danksagung |
|----------|--------|
| **[Claude Code](https://claude.ai)** — Unterstützt von Anthropic | Die primäre Entwicklungsplattform. AgentBridge wurde mit Claude Codes Agenten-Orchestrierungsfähigkeiten entworfen und gebaut. [Bedingungen](https://www.anthropic.com/legal) · [Datenschutz](https://www.anthropic.com/privacy) |
| **[OpenCode](https://opencode.ai)** | Terminal-Adapter-Ziel und Testpartner. Die OpenCode-CLI stellt die von AgentBridge's Terminal-Pool genutzte Ausführungsschnittstelle bereit. |
| **[MimoCode](https://mimo.ai)** | Terminal-Adapter-Ziel. Mimos CLI-Integration ermöglicht Multi-Modell-Frontend-Workflows. |
| **OpenAI Codex** | Terminal-Adapter-Ziel für programmierspezifische Aufgaben. |

### 🤖 Bei der Entwicklung verwendete KI-Modelle

- **Claude Opus 4.8 / Sonnet 4.6** (Anthropic) — Primäre Entwicklungsmodelle
- **Gemini 2.5 Flash** (Google) — Rechercheaufgaben, Wettbewerbsanalyse
- **GPT-4o** (OpenAI) — Architekturbewertung und -prüfung
- **DeepSeek V3** (DeepSeek) — Code-Review und Testen

### 📦 Open-Source-Abhängigkeiten

| Abhängigkeit | Lizenz | Zweck |
|------------|---------|---------|
| [Click](https://palletsprojects.com/p/click/) | BSD-3-Clause | CLI-Framework |
| [PyYAML](https://pyyaml.org/) | MIT | YAML-Parsing |
| [HTTPX](https://www.python-httpx.org/) | BSD-3-Clause | HTTP-Client für Modell-APIs |
| [pydantic](https://docs.pydantic.dev/) (geplant) | MIT | Konfigurationsvalidierung (v0.2) |

### 🧠 Fähigkeiten & Wissensquellen

- **ECC (Engineering Claude Code)** Plugin-System — Agenten-Orchestrierungsmuster
- **Claude Scholar** — Akademische Arbeitsablaufmuster
- **MCP (Model Context Protocol)** — Anthropics Protokoll für Tool-Integration

### 🌍 Community-Übersetzungen

AgentBridge README ist verfügbar in:
- [中文 (Chinese)](README_ZH.md)
- [Deutsch (German)](README_DE.md)
- [Français (French)](README_FR.md)
- [Español (Spanish)](README_ES.md)
- [日本語 (Japanese)](README_JP.md)
- [한국어 (Korean)](README_KR.md)

---

## 📄 Lizenz

[Apache 2.0](LICENSE) Copyright 2026 [jjjjjjjjnnjnn](https://github.com/jjjjjjjjnnjnn)

---

<p align="center">
  <strong>AgentBridge</strong> — Die Koordinationsschicht für KI-Agenten.<br>
  <sub>Mit ❤️ für die Open-Source-KI-Community entwickelt</sub>
</p>
