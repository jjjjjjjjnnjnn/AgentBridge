"""Workflow models — YAML-defined multi-agent pipelines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import yaml


@dataclass
class WorkflowStep:
    agent: str
    prompt: str
    model: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    mcp_tools: list[str] = field(default_factory=list)
    save_as: Optional[str] = None  # key to store result in shared memory
    system: Optional[str] = None


@dataclass
class Workflow:
    name: str = "untitled"
    description: str = ""
    steps: list[WorkflowStep] = field(default_factory=list)
    memory: Optional[dict] = None  # memory config override per workflow
    vars: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str) -> "Workflow":
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        steps = []
        for s in raw.get("steps", []):
            steps.append(WorkflowStep(
                agent=s.get("agent", "openai"),
                prompt=s.get("prompt", ""),
                model=s.get("model"),
                max_tokens=s.get("max_tokens"),
                temperature=s.get("temperature"),
                mcp_tools=s.get("mcp_tools", []),
                save_as=s.get("save_as"),
                system=s.get("system"),
            ))

        return cls(
            name=raw.get("name", "untitled"),
            description=raw.get("description", ""),
            steps=steps,
            memory=raw.get("memory"),
            vars=raw.get("vars", {}),
        )


def validate_workflow(wf: Workflow) -> list[str]:
    errors = []
    for i, step in enumerate(wf.steps):
        if not step.agent:
            errors.append(f"Step {i+1}: missing 'agent'")
        if not step.prompt:
            errors.append(f"Step {i+1}: missing 'prompt'")
    return errors
