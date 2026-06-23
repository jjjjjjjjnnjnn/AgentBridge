# Title: I built a system where multiple AI models collaborate like a real team

RelayOS is an open-source coordination layer for AI agents. It lets you create persistent AI workers across Claude, GPT, Gemini, DeepSeek and local models — with shared memory, workflow orchestration, and parallel execution.

## The Problem

If you use multiple AI tools daily, you know the pain:

1. Ask ChatGPT → copy output
2. Paste into Claude → copy again  
3. Paste into Gemini → copy again
4. Switch tabs 15 times per task

I was spending ~30% of my AI time on context switching, not actual work.

## What I Built

A CLI tool that treats each AI model as a "worker" in a team:

```bash
relayos terminal create google -n researcher
relayos terminal create anthropic -n architect
relayos terminal create openai -n coder

relayos run workflow.yaml
```

Four agents execute in parallel. Results accumulate in shared memory. No copy-pasting.

## How it works

- **Terminal pool**: Run multiple instances of the same CLI (e.g., 3 Claude Code terminals with different models)
- **Workflow engine**: YAML-defined pipelines with sequential/parallel steps
- **Shared memory**: Every agent sees previous agents' output
- **5 providers**: OpenAI, Anthropic, Google, DeepSeek, Ollama
- **MCP client**: Connect to any MCP server for tools

## Stack

Python CLI (Click), httpx-based adapters (no SDK bloat), SQLite persistence.

## Links

GitHub: https://github.com/jjjjjjjjnnjnn/relayos
Docs: pip install relayos

## What I'd love feedback on

- Would you use this in your daily workflow?
- What's missing for your use case?
- Which agent integrations matter most?

Happy to answer questions!
