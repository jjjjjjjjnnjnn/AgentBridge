"""Workflow engine — runs multi-agent pipelines with shared context."""
from __future__ import annotations

import logging
import re
from typing import Any

from agentmesh.adapters import get_adapter
from agentmesh.config import AgentMeshConfig
from agentmesh.memory.store import MemoryStore
from agentmesh.workflow.models import Workflow, WorkflowStep

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Executes multi-step YAML workflows across different agents."""

    def __init__(self, config: AgentMeshConfig, memory: MemoryStore | None = None):
        self.config = config
        self.memory = memory or MemoryStore(config.memory.get("path", "~/.agentmesh/memory.db"))

    def run(self, workflow: Workflow) -> list[dict[str, Any]]:
        results = []
        context = dict(workflow.vars) if workflow.vars else {}

        for i, step in enumerate(workflow.steps):
            logger.info(f"Step {i+1}/{len(workflow.steps)}: {step.agent}...")

            # Resolve template variables
            filled_prompt = self._resolve_template(step.prompt, context)
            system_msg = self._resolve_template(step.system or "", context) if step.system else None

            # Build messages with context
            messages = []
            if system_msg:
                messages.append({"role": "system", "content": system_msg})

            # Include previous step results as context
            if results:
                ctx_summary = self._build_context_summary(results)
                messages.append({"role": "system", "content": f"Previous steps:\n{ctx_summary}"})

            messages.append({"role": "user", "content": filled_prompt})

            # Get adapter and run
            provider_cfg = self.config.providers.get(step.agent, {})
            adapter = get_adapter(step.agent, {
                "api_key": self.config.resolve_api_key(step.agent),
                "model": step.model or provider_cfg.get("model", ""),
                "base_url": provider_cfg.get("base_url"),
                "max_tokens": step.max_tokens or provider_cfg.get("max_tokens", 4096),
                "temperature": step.temperature or provider_cfg.get("temperature", 0.7),
            })

            kwargs = {}
            if step.max_tokens:
                kwargs["max_tokens"] = step.max_tokens
            if step.temperature:
                kwargs["temperature"] = step.temperature

            response = adapter.chat_with_context(messages, **kwargs)

            step_result = {
                "step": i + 1,
                "agent": step.agent,
                "model": response.model,
                "prompt": filled_prompt,
                "content": response.content,
                "usage": response.usage,
            }
            results.append(step_result)

            # Save to memory
            key = step.save_as or f"step_{i+1}"
            self.memory.set(key, response.content)

            # Update context for next steps
            context[f"step_{i+1}"] = response.content
            if step.save_as:
                context[step.save_as] = response.content

            logger.info(f"  ✓ {response.model} ({response.usage.get('output_tokens', 0)} tokens)")

        return results

    def _resolve_template(self, text: str, context: dict) -> str:
        """Replace {{var}} placeholders with context values."""
        def replacer(m):
            key = m.group(1).strip()
            val = context.get(key, "")
            return str(val) if val is not None else m.group(0)
        return re.sub(r"\{\{(\w+)\}\}", replacer, text)

    def _build_context_summary(self, results: list[dict]) -> str:
        """Build a compact summary of previous step outputs."""
        parts = []
        for r in results:
            content = r["content"]
            if len(content) > 1000:
                content = content[:1000] + "\n... [truncated]"
            parts.append(f"--- Step {r['step']} ({r['agent']}) ---\n{content}")
        return "\n\n".join(parts)
