"""RelayOS Web Server — FastAPI-based dashboard and API."""
from __future__ import annotations

import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from relayos import __version__
from relayos.adapters import get_adapter, list_adapters
from relayos.config import load_config
from relayos.memory.store import MemoryStore
from relayos.orchestrator.pool import TerminalPool
from relayos.orchestrator.scheduler import Scheduler
from relayos.terminals import list_terminal_types
from relayos.workflow.engine import WorkflowEngine
from relayos.workflow.models import Workflow

logger = logging.getLogger(__name__)

# ── Pydantic models ────────────────────────────────────────────


class TerminalCreate(BaseModel):
    type_name: str
    name: Optional[str] = None
    model: Optional[str] = None


class PromptRequest(BaseModel):
    prompt: str
    model: Optional[str] = None


class WorkflowRun(BaseModel):
    yaml_content: str


class MemorySet(BaseModel):
    value: str
    session: Optional[str] = None

# ── App factory ─────────────────────────────────────────────────


def create_app(config_path: Optional[str] = None) -> FastAPI:
    """Create the FastAPI application with all routes."""
    app = FastAPI(title="RelayOS", version=__version__)

    cfg = load_config(Path(config_path) if config_path else None)
    pool = TerminalPool(config_path)
    memory = MemoryStore(cfg.memory.get("path", "~/.relayos/memory.db"))
    scheduler = Scheduler(pool, memory)
    engine = WorkflowEngine(cfg, memory)

    # ── Status ──────────────────────────────────────────────────

    @app.get("/api/status")
    async def get_status():
        return {
            "version": __version__,
            "terminals": pool.stats(),
            "adapters": list_adapters(),
            "terminal_types": [
                {"type": t["type"], "available": t["available"]}
                for t in list_terminal_types()
            ],
            "memory_keys": len(memory.get_all()),
        }

    # ── Terminals ───────────────────────────────────────────────

    @app.get("/api/terminals")
    async def list_terminals():
        return pool.list()

    @app.post("/api/terminals")
    async def create_terminal(req: TerminalCreate):
        inst = pool.create(type_name=req.type_name, name=req.name, model=req.model)
        return inst

    @app.get("/api/terminals/{terminal_id}")
    async def get_terminal(terminal_id: str):
        inst = pool.get(terminal_id)
        if not inst:
            raise HTTPException(status_code=404, detail="Terminal not found")
        return inst

    @app.post("/api/terminals/{terminal_id}/run")
    async def run_terminal(terminal_id: str, req: PromptRequest):
        inst = pool.get(terminal_id)
        if not inst:
            raise HTTPException(status_code=404, detail="Terminal not found")
        result = pool.run(terminal_id, req.prompt)
        return result

    @app.delete("/api/terminals/{terminal_id}")
    async def remove_terminal(terminal_id: str):
        ok = pool.remove(terminal_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Terminal not found")
        return {"ok": True}

    # ── Workflows ───────────────────────────────────────────────

    @app.post("/api/workflows/run")
    async def run_workflow(req: WorkflowRun):
        """Run a workflow from YAML content, stream progress via SSE."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(req.yaml_content)
            f.flush()
            wf_path = f.name

        wf = Workflow.from_yaml(wf_path)

        async def event_stream():
            results = []
            context = dict(wf.vars) if wf.vars else {}

            for i, step in enumerate(wf.steps):
                # Yield running status
                yield f"data: {json_dumps({'type': 'step_start', 'index': i, 'agent': step.agent, 'prompt': step.prompt[:80]})}\n\n"

                # Resolve template
                filled_prompt = step.prompt
                for k, v in context.items():
                    filled_prompt = filled_prompt.replace("{{" + k + "}}", str(v))

                messages = []
                if step.system:
                    messages.append({"role": "system", "content": step.system})
                if results:
                    ctx = "\n\n".join(
                        f"Step {r['step']} ({r['agent']}):\n{r['content'][:500]}"
                        for r in results
                    )
                    messages.append({"role": "system", "content": f"Previous context:\n{ctx}"})
                messages.append({"role": "user", "content": filled_prompt})

                try:
                    adapter = get_adapter(step.agent, {"api_key": cfg.resolve_api_key(step.agent)})
                    t0 = time.time()
                    resp = adapter.chat_with_context(messages)
                    duration = int((time.time() - t0) * 1000)

                    # Track cost
                    try:
                        usage = resp.usage or {}
                        cost_mgr.track(
                            provider=step.agent, model=resp.model,
                            input_tokens=usage.get("input_tokens", usage.get("prompt_tokens", 0)),
                            output_tokens=usage.get("output_tokens", usage.get("completion_tokens", 0)),
                        )
                    except Exception:
                        pass
                    results.append({
                        "step": i + 1, "agent": step.agent,
                        "model": resp.model, "content": resp.content,
                        "duration_ms": duration,
                    })
                    context[step.save_as or f"step_{i+1}"] = resp.content
                    yield f"data: {json_dumps({'type': 'step_done', 'index': i, 'agent': step.agent, 'model': resp.model, 'duration_ms': duration, 'chars': len(resp.content)})}\n\n"
                except Exception as e:
                    yield f"data: {json_dumps({'type': 'step_error', 'index': i, 'agent': step.agent, 'error': str(e)})}\n\n"

            yield f"data: {json_dumps({'type': 'complete', 'steps': len(results)})}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # ── Memory ──────────────────────────────────────────────────

    @app.get("/api/memory")
    async def list_memory():
        return [{"key": k, "preview": v[:100]} for k, v in memory.get_all().items()]

    @app.get("/api/memory/{key}")
    async def get_memory(key: str):
        val = memory.get(key)
        if val is None:
            raise HTTPException(status_code=404, detail="Key not found")
        return {"key": key, "value": val}

    @app.post("/api/memory/{key}")
    async def set_memory(key: str, req: MemorySet):
        memory.set(key, req.value, req.session)
        return {"ok": True}

    @app.delete("/api/memory/{key}")
    async def delete_memory(key: str):
        memory.set(key, None)
        return {"ok": True}

    # ── Cost ────────────────────────────────────────────────────

    from relayos.cost import CostManager
    cost_mgr = CostManager()

    @app.get("/api/cost")
    async def get_cost_report():
        return cost_mgr.get_report()

    # ── Router ───────────────────────────────────────────────────

    from relayos.core.router import FlowRouter
    flow_router = FlowRouter()

    @app.post("/api/router/analyze")
    async def analyze_route(data: dict):
        prompt = data.get("prompt", "")
        policy = data.get("policy", "balanced")
        decision = flow_router.route(prompt, policy=policy)
        return {
            "provider": decision.provider,
            "task_type": decision.task_type,
            "confidence": decision.confidence,
            "reason": decision.reason,
            "estimated_tokens": decision.estimated_tokens,
        }

    # ── Inbox ────────────────────────────────────────────────────

    from relayos.core.inbox import WorkerInbox
    inbox_mgr = WorkerInbox()

    @app.post("/api/inbox/send")
    async def inbox_send(data: dict):
        mid = inbox_mgr.send(
            to=data["to"],
            body=data["body"],
            subject=data.get("subject", ""),
            from_worker=data.get("from_worker", "system"),
        )
        return {"message_id": mid}

    @app.get("/api/inbox/{worker}")
    async def inbox_list(worker: str):
        return {"messages": inbox_mgr.list_inbox(worker), "unread": inbox_mgr.count_unread(worker)}

    @app.get("/api/inbox/stats")
    async def inbox_stats():
        return inbox_mgr.get_stats()

    # ── Workers ───────────────────────────────────────────────────

    from relayos.core.worker import WorkerManager
    worker_mgr = WorkerManager(config_path)

    @app.get("/api/workers")
    async def list_workers():
        return worker_mgr.get_team()

    @app.post("/api/workers")
    async def create_worker(data: dict):
        name = data.get("name", "")
        role = data.get("role", "assistant")
        from relayos.core.worker import DEFAULT_ROLES
        role_def = DEFAULT_ROLES.get(role, DEFAULT_ROLES["assistant"])
        w = worker_mgr.create(
            name=name, role=role,
            provider=role_def["provider"],
            model=role_def["model"],
            emoji=role_def.get("emoji", "🤖"),
            description=role_def.get("description", ""),
        )
        return {"name": w.name, "role": w.role, "status": w.status}

    @app.get("/api/workers/stats")
    async def worker_stats():
        return worker_mgr.stats()

    # ── Frontend ────────────────────────────────────────────────

    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        @app.get("/")
        async def index():
            return FileResponse(static_dir / "index.html")

        @app.get("/trace")
        async def trace():
            return FileResponse(static_dir / "trace.html")

        @app.get("/workers")
        async def workers():
            return FileResponse(static_dir / "workers.html")

        @app.get("/{path:path}")
        async def static_files(path: str):
            fp = static_dir / path
            if fp.exists() and fp.is_file():
                return FileResponse(fp)
            return FileResponse(static_dir / "index.html")

    return app


def json_dumps(obj: Any) -> str:
    """Fast JSON serialize for SSE."""
    import json
    return json.dumps(obj, ensure_ascii=False, default=str)
