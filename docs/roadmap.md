# AgentMesh Roadmap

## v0.1.0 — "Alpha" (Week 1)

**Goal**: Usable CLI for multi-agent workflows with shared memory.

- [ ] Agent Adapters: OpenAI, Claude, Gemini, Ollama, DeepSeek
- [ ] YAML Workflow Engine: sequential multi-step pipelines
- [ ] Shared Memory: SQLite-based context passing between agents
- [ ] MCP Client: consume external MCP servers for tools
- [ ] CLI: `agentmesh run workflow.yaml`

**Size**: ~1000-1500 lines
**Position**: "Stop copy-pasting between AI tools."

## v0.2.0 — "Beta" (Week 2)

**Goal**: Web UI + cost-aware routing.

- [ ] Web Dashboard (Next.js): view workflow runs, agent status
- [ ] Cost Manager: free-first routing policy
- [ ] Docker Compose: one-command deploy
- [ ] 10+ example workflows included
- [ ] LinguaGraph integration showcase

## v0.5.0 — "Flow" (Week 3)

**Goal**: Advanced orchestration.

- [ ] LangGraph-powered state machine
- [ ] Conditional branching in workflows
- [ ] Human-in-the-loop checkpoints
- [ ] MCP Router: pass-through to connected agents
- [ ] Streaming output (SSE)

## v1.0.0 — "Mesh" (Week 4+)

**Goal**: Production-ready bidirectional MCP Hub.

- [ ] Bidirectional MCP Hub (Server + Client)
- [ ] Plugin system for community adapters
- [ ] Postgres upgrade path
- [ ] Vector memory (Chroma/Qdrant)
- [ ] Comprehensive testing
- [ ] API stability

## Non-Goals (Pre-v1.0)

- User auth / multi-tenant
- Drag-and-drop workflow editor
- Plugin marketplace
- Mobile app
- OpenTelemetry tracing
- TypeScript SDK
