"""Workflow scheduler — dispatches tasks across terminal pool."""
from __future__ import annotations

import logging
from typing import Any, Optional

from agentbridge.memory.store import MemoryStore
from agentbridge.orchestrator.pool import TerminalPool
from agentbridge.terminals.base import TerminalResult

logger = logging.getLogger(__name__)


class Scheduler:
    """Schedules workflow steps across available terminals.

    Supports:
    - Run steps sequentially (pipeline)
    - Run steps in parallel (fan-out)
    - Auto-dispatch to appropriate terminal type
    """

    def __init__(self, pool: TerminalPool, memory: Optional[MemoryStore] = None):
        self.pool = pool
        self.memory = memory or MemoryStore("~/.agentbridge/memory.db")

    def run_sequential(self, steps: list[dict[str, Any]]) -> list[TerminalResult]:
        """Run steps sequentially, passing context between them."""
        results = []
        context = {}

        for i, step in enumerate(steps):
            prompt = step.get("prompt", "")
            terminal_type = step.get("agent") or step.get("terminal_type", "claude")
            terminal_id = step.get("terminal_id")
            save_as = step.get("save_as")
            model = step.get("model")

            # Resolve template variables {{key}}
            for k, v in context.items():
                prompt = prompt.replace("{{" + k + "}}", str(v))

            logger.info(f"Step {i+1}/{len(steps)}: dispatch to {terminal_type}...")

            if terminal_id:
                result = self.pool.run(terminal_id, prompt, model=model)
            else:
                # Create a temporary terminal for this step, then clean up
                inst = self.pool.create(terminal_type, model=model)
                try:
                    result = self.pool.run(inst.id, prompt)
                finally:
                    self.pool.remove(inst.id)

            # Store result
            key = save_as or f"step_{i+1}"
            self.memory.set(key, result.content)
            context[key] = result.content
            context[f"step_{i+1}"] = result.content
            results.append(result)

            status = "[OK]" if result.exit_code == 0 else f"[ERR] {result.error}"
            logger.info(f"  Step {i+1} {status} ({result.duration_ms}ms, {len(result.content)} chars)")

        return results

    def run_parallel(self, steps: list[dict[str, Any]]) -> list[TerminalResult]:
        """Run multiple independent steps in parallel."""
        tasks = []
        for step in steps:
            tasks.append({
                "terminal_type": step.get("agent") or step.get("terminal_type", "claude"),
                "terminal_id": step.get("terminal_id"),
                "prompt": step.get("prompt", ""),
            })

        logger.info(f"Parallel dispatch: {len(tasks)} tasks")
        results = self.pool.run_parallel(tasks)

        for i, (step, result) in enumerate(zip(steps, results)):
            save_as = step.get("save_as")
            if save_as:
                self.memory.set(save_as, result.content)
            status = "[OK]" if result.exit_code == 0 else f"[ERR] {result.error}"
            logger.info(f"  Task {i+1}: {step.get('agent')} {status}")

        return results

    def run_workflow_yaml(self, steps: list[dict], parallel: bool = False):
        """Run a workflow from parsed YAML steps."""
        if parallel:
            return self.run_parallel(steps)
        else:
            return self.run_sequential(steps)
