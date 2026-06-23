<p align="center">
  <picture>
    <img src="https://img.shields.io/badge/RelayOS-v0.1.0a1-8B5CF6?style=for-the-badge" alt="RelayOS">
  </picture>
</p>

<h1 align="center">RelayOS</h1>

<p align="center">
  <strong>Deja de copiar y pegar entre herramientas de IA.</strong><br>
  Crea trabajadores de IA persistentes en Claude, GPT, Gemini, DeepSeek y modelos locales —<br>
  con memoria compartida, orquestación de flujos de trabajo e integración MCP.
</p>

<p align="center">
  <a href="#-inicio-rápido"><img src="https://img.shields.io/badge/-Inicio_rápido-10B981?style=flat-square" alt="Inicio rápido"></a>
  <a href="#-características"><img src="https://img.shields.io/badge/-Características-3B82F6?style=flat-square" alt="Características"></a>
  <a href="#%EF%B8%8F-configuración"><img src="https://img.shields.io/badge/-Configuración-8B5CF6?style=flat-square" alt="Configuración"></a>
  <a href="#-ejemplos"><img src="https://img.shields.io/badge/-Ejemplos-F59E0B?style=flat-square" alt="Ejemplos"></a>
  <a href="#%EF%B8%8F-arquitectura"><img src="https://img.shields.io/badge/-Arquitectura-EC4899?style=flat-square" alt="Arquitectura"></a>
  <a href="#%EF%B8%8F-creditos"><img src="https://img.shields.io/badge/-Créditos-6366F1?style=flat-square" alt="Créditos"></a>
  <a href="README_ZH.md"><img src="https://img.shields.io/badge/中文-文档-EA4335?style=flat-square" alt="中文"></a>
  <a href="README_DE.md"><img src="https://img.shields.io/badge/Deutsch-Dokument-FFD700?style=flat-square" alt="Deutsch"></a>
  <a href="README_ES.md"><img src="https://img.shields.io/badge/Español-Doc-00C853?style=flat-square" alt="Español"></a>
  <a href="README_FR.md"><img src="https://img.shields.io/badge/Français-Doc-1E90FF?style=flat-square" alt="Français"></a>
  <a href="README_JP.md"><img src="https://img.shields.io/badge/日本語-ドキュメント-FF4081?style=flat-square" alt="日本語"></a>
  <a href="README_KR.md"><img src="https://img.shields.io/badge/한국어-문서-03C75A?style=flat-square" alt="한국어"></a>
</p>

---

## 📋 Índice

| Sección | Descripción |
|---------|-------------|
| [🎯 Visión general](#-visión-general) | Qué es RelayOS y por qué existe |
| [✨ Características](#-características) | Capacidades actuales |
| [⚡ Inicio rápido](#-inicio-rápido) | Instala y ejecuta tu primer flujo de trabajo |
| [📖 Guía de usuario](#-guía-de-usuario) | Flujos de trabajo, terminales, memoria |
| [⚙️ Configuración](#%EF%B8%8F-configuración) | Proveedores, terminales, enrutamiento |
| [🏗️ Arquitectura](#%EF%B8%8F-arquitectura) | Diseño del sistema |
| [📁 Ejemplos](#-ejemplos) | Flujos de trabajo listos para usar |
| [🛣️ Hoja de ruta](#%EF%B8%8F-hoja-de-ruta) | Planes futuros |
| [🙏 Créditos](#%EF%B8%8F-creditos) | Agradecimientos |
| [📄 Licencia](#-licencia) | Apache 2.0 |

---

## 🎯 Visión general

**RelayOS** es una capa de coordinación de código abierto para agentes de IA — como Docker para contenedores, pero para herramientas de IA.

### El problema

Usas **Claude Code** para arquitectura, **ChatGPT** para razonamiento, **Gemini** para investigación, **DeepSeek** para programar. Cada herramienta es excelente. **No se comunican entre sí.** Pierdes el 30 % de tu tiempo copiando contexto entre herramientas y quemando tokens premium en tareas que un modelo gratuito podría realizar.

### La solución

```
┌─────────────────────────────────────────────────────┐
│                 Tus herramientas IA                   │
│   Claude Code    ChatGPT    Gemini    DeepSeek       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                   RelayOS                        │
│                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │  Pool de    │  │  Motor de   │  │  Memoria    │  │
│  │  Terminales │  │  Flujo de   │  │  Compartida │  │
│  │ (Multi-CLI) │  │  Trabajo    │  │  (SQLite)   │  │
│  │             │  │  (YAML)     │  │             │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │  Adaptadores │  │ Cliente MCP │                    │
│  │ (5 proveed.) │  │ (Herramientas)│                  │
│  └─────────────┘  └─────────────┘                    │
└──────────────────────────────────────────────────────┘
```

---

## ✨ Características

### 🤖 Pool de terminales múltiples
- Ejecuta **múltiples instancias** de la misma herramienta CLI (p. ej., 3 terminales de Claude Code simultáneamente)
- Cada terminal tiene una **selección de modelo independiente**
- **Persistente** entre sesiones (respaldado por SQLite)

**Terminales compatibles:** `claude`, `mimo`, `opencode`, `codex`, `qcode`, `custom`

### 🔄 Motor de flujo de trabajo
- Tuberías **secuenciales** con resolución de variables de plantilla entre pasos
- Ejecución **paralela** en múltiples terminales simultáneamente
- Flujos de trabajo definidos en YAML — sin necesidad de programar

### 🧠 Memoria compartida
- **Contexto entre agentes:** cada agente ve la salida de los agentes anteriores
- **Persistencia SQLite:** la memoria sobrevive entre sesiones
- **Claves nombradas:** `save_as` para referencia semántica

### 🔗 Integración MCP
- Conéctate a **cualquier servidor MCP** para obtener herramientas
- Cliente MCP basado en stdio con tiempo de espera y manejo de errores

### 💰 Enrutamiento consciente de costos (planificado)
- Modelos gratuitos primero, de pago solo cuando sea necesario
- Enrutamiento por política (calidad vs velocidad vs costo)

---

## ⚡ Inicio rápido

### Instalación

```bash
pip install relayos
```

### Inicialización

```bash
relayos init
```

Configura tus claves API mediante variables de entorno:

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GEMINI_API_KEY="..."
export DEEPSEEK_API_KEY="sk-..."
```

### Ejecuta tu primer flujo de trabajo

Crea un archivo `hello.yaml`:

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

Ejecútalo:

```bash
relayos run hello.yaml
```

### Gestionar terminales

```bash
# Ver qué terminales están disponibles
relayos terminal types

# Crear un terminal Claude Code para arquitectura
relayos terminal create claude -n architect -m claude-sonnet-4-20250514

# Y otro para tareas rápidas
relayos terminal create claude -n assistant -m claude-haiku-4-20251001

# Crear un terminal Gemini para investigación
relayos terminal create google -n researcher -m gemini-2.5-flash

# Ver todos los terminales en ejecución
relayos terminal list

# Ejecutar un prompt en un terminal específico
relayos terminal exec opencode "Analyze this data"
```

---

## 📖 Guía de usuario

### Flujos de trabajo

Los flujos de trabajo son archivos YAML que definen tuberías multi-agente:

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

| Campo | Descripción |
|-------|-------------|
| `agent` | Tipo de terminal a utilizar (anthropic, google, openai, opencode, deepseek) |
| `prompt` | El prompt a enviar |
| `save_as` | Clave para almacenar el resultado en la memoria compartida |
| `system` | Prompt del sistema (opcional) |
| `model` | Sobrescritura de modelo (opcional) |
| `parallel` | Establecer `true` para ejecutar el paso en un grupo paralelo |

### Terminales

RelayOS trata cada CLI de IA como un "terminal" — un trabajador independiente:

| Terminal | Binario | Modelo por defecto | Estado |
|----------|--------|---------------|--------|
| `claude` | `claude` | claude-sonnet-4-20250514 | ✅ Disponible |
| `mimo` | `mimo` | gpt-4o | ✅ Disponible |
| `opencode` | `opencode` | deepseek-chat | ✅ Disponible |
| `codex` | `codex` | gpt-4o | ❌ No instalado |
| `qcode` | `q` | qwen2.5:7b | ❌ No instalado |
| `custom` | (configurable) | definido por el usuario | ⚡ Personalizado |

### Memoria compartida

```bash
# Almacenar
relayos remember my_key "some value"

# Recuperar
relayos recall my_key

# Listar todas las claves
relayos memory-list
```

---

## ⚙️ Configuración

Ubicación del archivo de configuración: `~/.relayos/config.yaml` (o `$RELAYOS_CONFIG_DIR/config.yaml`)

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

**Prioridad de claves API:**
1. Campo `api_key` en el archivo de configuración
2. Variable de entorno (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)
3. Vacío (el adaptador mostrará una advertencia)

---

## 🏗️ Arquitectura

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
                    │  │  Pool de       │──│──→ Claude Code, Mimo, OpenCode...
                    │  │  Terminales    │  │
                    │  │  (Multi-Inst.) │  │
                    │  ├────────────────┤  │
                    │  │ Motor de       │  │
                    │  │ Flujo de       │  │
                    │  │ Trabajo(YAML)  │  │
                    │  ├────────────────┤  │
                    │  │  Planificador   │──│──→ Secuencial / Paralelo
                    │  ├────────────────┤  │
                    │  │ Memoria        │  │
                    │  │ Compartida     │  │
                    │  │ (SQLite)       │  │
                    │  ├────────────────┤  │
                    │  │  Adaptadores    │──│──→ OpenAI / Claude / Gemini...
                    │  ├────────────────┤  │
                    │  │ Cliente MCP    │──│──→ GitHub MCP / Filesystem MCP...
                    │  └────────────────┘  │
                    └──────────────────────┘
```

### Decisiones de diseño

| Decisión | Elección | Justificación |
|----------|--------|-----------|
| CLI primero | Click + YAML | Flujos de trabajo sin código; los no desarrolladores pueden crear tuberías |
| Multi-instancia | Pool de hilos | Ejecutar agentes concurrentes en diferentes modelos |
| Persistencia | SQLite | Memoria entre sesiones sin dependencias externas |
| Adaptadores | Basado en httpx | Dependencias mínimas; sin SDK de proveedores |
| MCP | Solo cliente (v0.1) | Consumir servidores MCP; modo Hub en v1.0 |

---

## 📁 Ejemplos

| Ejemplo | Descripción |
|---------|-------------|
| `examples/saas-builder.yaml` | Tubería SaaS de 4 agentes: Gemini investigación → Claude diseño → GPT código → DeepSeek revisión |
| `examples/linguagraph-research.yaml` | Tubería de investigación de 3 agentes: análisis lingüístico → modelo cognitivo → escritura de artículo |
| `examples/debate.yaml` | Debate de 3 agentes: LLM pro-local vs pro-nube, juzgado por Gemini |
| `examples/parallel-research.yaml` | Sprint de investigación paralela de 4 agentes con síntesis |

---

## 🛣️ Hoja de ruta

- **v0.1** — ✅ CLI, flujos de trabajo YAML, 5 adaptadores, memoria compartida, cliente MCP, pool de terminales
- **v0.2** — 🔄 Panel web (Next.js), visualización de flujos de trabajo, enrutamiento consciente de costos, Docker
- **v0.5** — 🔄 Orquestación LangGraph, ramificación condicional, intervención humana
- **v1.0** — 🔄 Hub MCP bidireccional, sistema de plugins, memoria vectorial

---

## 🙏 Créditos

RelayOS está construido sobre hombros de gigantes. Expresamos nuestro más profundo agradecimiento a:

### 🖥️ Plataformas terminales

| Plataforma | Crédito |
|----------|--------|
| **[Claude Code](https://claude.ai)** — Desarrollado por Anthropic | La plataforma de desarrollo principal. RelayOS fue diseñado y construido utilizando las capacidades de orquestación de agentes de Claude Code. [Términos](https://www.anthropic.com/legal) · [Privacidad](https://www.anthropic.com/privacy) |
| **[OpenCode](https://opencode.ai)** | Destino del adaptador de terminal y socio de pruebas. La CLI de OpenCode proporciona la interfaz de ejecución utilizada por el pool de terminales de RelayOS. |
| **[MimoCode](https://mimo.ai)** | Destino del adaptador de terminal. La integración CLI de Mimo permite flujos de trabajo frontend multimodelo. |
| **OpenAI Codex** | Destino del adaptador de terminal para tareas de codificación. |

### 🤖 Modelos de IA utilizados en el desarrollo

- **Claude Opus 4.8 / Sonnet 4.6** (Anthropic) — Modelos principales de desarrollo
- **Gemini 2.5 Flash** (Google) — Tareas de investigación, análisis competitivo
- **GPT-4o** (OpenAI) — Evaluación y revisión de arquitectura
- **DeepSeek V3** (DeepSeek) — Revisión de código y pruebas

### 📦 Dependencias de código abierto

| Dependencia | Licencia | Propósito |
|------------|---------|---------|
| [Click](https://palletsprojects.com/p/click/) | BSD-3-Clause | Framework CLI |
| [PyYAML](https://pyyaml.org/) | MIT | Análisis YAML |
| [HTTPX](https://www.python-httpx.org/) | BSD-3-Clause | Cliente HTTP para APIs de modelos |
| [pydantic](https://docs.pydantic.dev/) (planificado) | MIT | Validación de configuración (v0.2) |

### 🧠 Habilidades y fuentes de conocimiento

- **ECC (Engineering Claude Code)** Sistema de plugins — patrones de orquestación de agentes
- **Claude Scholar** — Patrones de flujo de trabajo de investigación académica
- **MCP (Model Context Protocol)** — Protocolo de Anthropic para integración de herramientas

### 🌍 Traducciones de la comunidad

El README de RelayOS está disponible en:
- [中文 (Chinese)](README_ZH.md)
- [Deutsch (German)](README_DE.md)
- [Français (French)](README_FR.md)
- [Español (Spanish)](README_ES.md)
- [日本語 (Japanese)](README_JP.md)
- [한국어 (Korean)](README_KR.md)

---

## 📄 Licencia

[Apache 2.0](LICENSE) Copyright 2026 [jjjjjjjjnnjnn](https://github.com/jjjjjjjjnnjnn)

---

<p align="center">
  <strong>RelayOS</strong> — La capa de coordinación para agentes de IA.<br>
  <sub>Construido con ❤️ para la comunidad de IA de código abierto</sub>
</p>
