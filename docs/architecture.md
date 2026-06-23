# RelayOS Architecture

## Current (v0.1 — Alpha)

```
User
 │
 ▼
relayos run workflow.yaml
 │
 ▼
┌─────────────────────────────────────┐
│         RelayOS Runtime            │
│                                      │
│  ┌──────────┐  ┌───────────────┐    │
│  │ Workflow  │─▶│ Agent Adapter │    │
│  │ Engine    │  │ Layer         │    │
│  │ (YAML)    │  │               │    │
│  └──────────┘  │ OpenAI        │    │
│       │        │ Claude        │    │
│       ▼        │ Gemini        │    │
│  ┌──────────┐  │ Ollama        │    │
│  │  Memory  │  │ DeepSeek      │    │
│  │  Layer   │  └───────┬───────┘    │
│  │ (SQLite) │          │           │
│  └──────────┘          ▼           │
│                   ┌──────────┐     │
│                   │MCP Client│     │
│                   └──────────┘     │
└─────────────────────────────────────┘
```

## Planned (v1.0)

```
Claude Code / Cursor / ChatGPT / Any MCP Client
 │                    │                     │
 └────────────────────┼─────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────┐
│           RelayOS Gateway                 │
│         (MCP Server + REST API)             │
└──────────────────┬─────────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────┐
│           RelayOS Runtime                  │
│                                              │
│  ┌──────────────┐  ┌────────────────────┐   │
│  │ Routing      │  │ Cost Manager       │   │
│  │ Engine       │  │ (free-first policy)│   │
│  │ (LangGraph)  │  └────────────────────┘   │
│  └──────┬───────┘                            │
│         │                                    │
│  ┌──────▼────────────────────────────────┐   │
│  │         Agent Adapter Layer            │   │
│  │  OpenAI │ Claude │ Gemini │ DeepSeek  │   │
│  │  Ollama │ ...    │ (pluggable)        │   │
│  └──────┬───────────────────────────────┘   │
│         │                                    │
│  ┌──────▼──────────┐  ┌─────────────────┐   │
│  │  Shared Memory   │  │ MCP Hub          │   │
│  │ (Vector + SQLite)│  │ (Server + Client) │   │
│  └─────────────────┘  └─────────────────┘   │
└──────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. YAML-first workflow (v0.1)

Workflows defined as YAML, not code. Enables non-developers to create multi-agent pipelines without writing Python.

### 2. Dict + SQLite memory (v0.1)

Vector search is overkill for v0.1. Simple key-value with SQLite persistence covers 80% of use cases.

### 3. Plug-in Architecture

Each agent adapter is a standalone Python class registered via entry_points. Adding a new provider requires zero changes to core.

### 4. MCP Consumer (v0.1) → Hub (v1.0)

Start by consuming MCP servers for tools. Graduate to exposing RelayOS as an MCP server. Finally become a full bidirectional hub.

## Data Flow

```
1. User runs: relayos run workflow.yaml
2. Workflow Engine parses steps
3. For each step, Agent Adapter calls the selected provider
4. Memory layer stores/retrieves context automatically
5. MCP Client provides tools if configured
6. Results accumulate across steps
7. Final output written to stdout/file
```
