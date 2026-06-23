# [Project] RelayOS — open-source multi-agent orchestrator (Claude + GPT + Gemini + local models)

**GitHub**: https://github.com/jjjjjjjjnnjnn/relayos  
**Install**: `pip install relayos`

## What is it?

A CLI tool that coordinates multiple AI models as persistent workers with shared memory and workflow orchestration.

## Key features

- **Multi-terminal pool**: Run multiple AI CLIs simultaneously (Claude Code, Mimo, OpenCode, etc.)
- **Per-instance model selection**: Each terminal can use a different model
- **YAML workflows**: Sequential and parallel pipelines with template variables
- **Shared memory**: Cross-agent context persistence (SQLite)
- **5 provider adapters**: OpenAI, Anthropic, Google, DeepSeek, Ollama (local)
- **MCP client**: Connect to any MCP server for tools

## Quick demo

```bash
# Install
pip install relayos
relayos init

# Create a 3-step research workflow
cat > research.yaml << 'EOF'
name: "Research Pipeline"
steps:
  - agent: google
    prompt: "Research latest multi-agent AI frameworks"
  - agent: anthropic  
    prompt: "Design architecture based on the research"
  - agent: openai
    prompt: "Generate implementation plan"
EOF

# Run it
relayos run research.yaml
```

## Why I built this

I use Claude Code, ChatGPT, Gemini, and DeepSeek daily. Copy-pasting between them was killing my flow. Now I let them collaborate automatically.

The local model support (Ollama) is important — you can route sensitive tasks to local models and use cloud APIs for heavy lifting.

## Tech

Python, Click CLI, httpx, SQLite, YAML, Apache 2.0 license.

Would love feedback, issues, and PRs!
