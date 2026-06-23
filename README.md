# AgentMesh

> **Stop copy-pasting between AI tools.**
>
> AgentMesh lets Claude, GPT, Gemini, DeepSeek and local models collaborate through shared memory, workflows and MCP.

## The Problem

You use Claude Code for architecture, ChatGPT for reasoning, Gemini for research, DeepSeek for coding. Each is excellent. They don't talk to each other.

You copy-paste. You waste tokens on the wrong model. You have no shared context.

## The Solution

AgentMesh is the **coordination layer** for AI agents — like Docker for containers, but for AI.

```
                   ┌─────────────┐
                   │  Your AI    │
                   │  Tools      │
                   └──────┬──────┘
                          │
               ┌──────────┴──────────┐
               │    AgentMesh         │
               │   ┌──────────────┐   │
               │   │  Workflow    │   │
               │   │  Engine      │   │
               │   ├──────────────┤   │
               │   │ Shared Mem   │   │
               │   ├──────────────┤   │
               │   │ MCP Client   │   │
               │   └──────────────┘   │
               └──────────┬──────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
     Claude Code      ChatGPT        Local LLM
     (your tools)   (your tools)    (Ollama)
```

## Quick Start

```bash
pip install agentmesh

# Create a workflow
cat > workflow.yaml << EOF
steps:
  - agent: gemini
    prompt: "Research MCP protocol latest updates"

  - agent: claude
    prompt: "Based on the research above, design architecture"
EOF

# Run it
agentmesh run workflow.yaml
```

## Features

- **Multi-agent Workflows**: Chain Claude → GPT → Gemini in one pipeline
- **Shared Memory**: Each agent sees previous agents' output
- **MCP Integration**: Connect any MCP server for tools
- **Cost-aware Routing**: Free models first, paid only when needed
- **Provider-agnostic**: OpenAI, Anthropic, Google, DeepSeek, Ollama
- **Self-hosted**: Your API keys, your data, your infrastructure

## Install

```bash
pip install agentmesh
```

Or with Docker:

```bash
docker run -v $(pwd):/workspace agentmesh run workflow.yaml
```

## Configuration

```yaml
# ~/.agentmesh/config.yaml
providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4o
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    model: claude-sonnet-4-20250514
  google:
    api_key: ${GEMINI_API_KEY}
    model: gemini-2.5-flash
  ollama:
    model: qwen2.5:7b
    base_url: http://localhost:11434

routing:
  default: balanced
  policies:
    coding: free_first
    research: quality_first
    quick: cheapest
```

## Example: Multi-Agent SaaS Builder

```yaml
steps:
  - agent: gemini
    prompt: "Research competitors for an AI note-taking SaaS"
    
  - agent: claude
    prompt: "Design system architecture based on: {{output}}"
    
  - agent: gpt
    prompt: "Implement the core API described in: {{output}}"
    
  - agent: deepseek
    prompt: "Review this code for bugs and security: {{output}}"
```

## Roadmap

- **v0.1** — CLI + YAML workflows + Shared memory + MCP client
- **v0.2** — Web UI + Cost-aware routing + Docker
- **v0.5** — LangGraph orchestration + Conditional branching
- **v1.0** — Bidirectional MCP Hub + Plugin system + Vector memory

## License

MIT
