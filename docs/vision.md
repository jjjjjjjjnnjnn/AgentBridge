# RelayOS — The Operating System for AI Agents

## Problem

Every AI tool today is an island.

You use Claude Code for architecture, ChatGPT for reasoning, Gemini for research, DeepSeek for coding. Each is excellent at what it does. But they don't talk to each other. You copy-paste context between them. You waste 30% of your time on manual handoff. You burn premium tokens on tasks a free model could handle.

The AI ecosystem has a proliferation of clients (Claude Code, Cursor, ChatGPT, Gemini, Open WebUI, Cherry Studio...) but **no coordination layer** between them. The MCP protocol solves the tool-access problem but not the multi-agent coordination problem.

## Solution

RelayOS is the coordination layer for AI agents.

It sits **between** your AI tools and the models they call. Like Docker orchestrates containers, RelayOS orchestrates agents — routing tasks to the right model, maintaining shared memory, managing costs, and connecting MCP tools — all while letting you keep using the tools you already love.

## Principles

1. **Infrastructure, not a client.** Users keep their existing tools (Claude Code, Cursor, ChatGPT). RelayOS works underneath.
2. **Router, not an aggregator.** Not "one UI to rule them all" — but "intelligent routing to the right agent."
3. **Cost-aware by default.** Free tiers first, paid only when needed.
4. **MCP-native.** MCP is the universal protocol. RelayOS is both consumer and provider.
5. **Open source MIT.** No vendor lock-in, no hidden pricing.

## Target

```
Primary: AI-integrated developer using 3+ AI tools daily
Secondary: Small team wanting unified agent infrastructure
Tertiary: MCP server builders seeking distribution
```

## Core Metaphor

> RelayOS is to AI agents what Docker is to containers:
> a runtime, a routing layer, and an ecosystem — not the app itself.
