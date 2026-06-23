"""Execution Planner — decomposes tasks into multi-step execution graphs.

Takes a user's natural language task and produces an optimized
execution plan: a DAG of steps, each assigned to the optimal model.

Example:
    "Implement JWT auth in FastAPI"
    →
    [1] Research best practices     → gemini (free)
    [2] Design architecture         → claude (quality)
    [3] Implement core logic        → opencode (free)
    [4] Security review             → deepseek (cheap)
    [5] Final integration test      → claude (final review)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from relayos.core.capabilities import PROVIDER_DEFAULT_MODEL
from relayos.core.scheduler import ModelScheduler
from relayos.terminals.scheduler import best_terminal


@dataclass
class ExecutionStep:
    id: str
    description: str
    task_type: str
    model: str = ""
    terminal: str = ""
    provider: str = ""
    estimated_cost: float = 0.0
    depends_on: list[str] = field(default_factory=list)
    prompt_template: str = ""
    status: str = "pending"  # pending | running | done | error


@dataclass
class ExecutionPlan:
    task: str
    steps: list[ExecutionStep]
    total_estimated_cost: float = 0.0
    total_steps: int = 0


# Task decomposition patterns
# Each pattern defines sub-steps for a given task type
TASK_PATTERNS: dict[str, list[dict]] = {
    "coding": [
        {"id": "requirements", "description": "Analyze requirements", "task_type": "research",
         "prompt": "Analyze the requirements for: {task}. List functional and non-functional requirements."},
        {"id": "architecture", "description": "Design architecture", "task_type": "architecture",
         "prompt": "Based on requirements, design the architecture for: {task}", "depends_on": ["requirements"]},
        {"id": "implementation", "description": "Implement the solution", "task_type": "coding",
         "prompt": "Implement: {task} following the architecture. Write complete, production-ready code.",
         "depends_on": ["architecture"]},
        {"id": "review", "description": "Review and refine", "task_type": "review",
         "prompt": "Review the implementation for: {task}. Check for bugs, edge cases, and improvements.",
         "depends_on": ["implementation"]},
    ],
    "architecture": [
        {"id": "research", "description": "Research requirements & constraints", "task_type": "research",
         "prompt": "Research the architecture requirements for: {task}"},
        {"id": "design", "description": "Design system architecture", "task_type": "architecture",
         "prompt": "Design a complete system architecture for: {task}. Include components, data flow, tech stack.",
         "depends_on": ["research"]},
        {"id": "review", "description": "Review architecture decisions", "task_type": "review",
         "prompt": "Review this architecture for: {task}. Check consistency, scalability, and trade-offs.",
         "depends_on": ["design"]},
    ],
    "research": [
        {"id": "gather", "description": "Gather information", "task_type": "research",
         "prompt": "Research and gather information about: {task}"},
        {"id": "analyze", "description": "Analyze findings", "task_type": "reasoning",
         "prompt": "Analyze the research findings for: {task}. Identify patterns, insights, and conclusions.",
         "depends_on": ["gather"]},
        {"id": "report", "description": "Write summary", "task_type": "writing",
         "prompt": "Write a clear, concise summary of: {task} based on the analysis.",
         "depends_on": ["analyze"]},
    ],
    "review": [
        {"id": "analyze", "description": "Analyze the subject", "task_type": "review",
         "prompt": "Review: {task}. Check for issues, improvements, and best practices."},
        {"id": "report", "description": "Document findings", "task_type": "writing",
         "prompt": "Document the review findings for: {task}. Prioritize issues by severity.",
         "depends_on": ["analyze"]},
    ],
    "writing": [
        {"id": "research", "description": "Research topic", "task_type": "research",
         "prompt": "Research the topic: {task}"},
        {"id": "draft", "description": "Write first draft", "task_type": "writing",
         "prompt": "Write a draft about: {task}", "depends_on": ["research"]},
        {"id": "refine", "description": "Polish and format", "task_type": "review",
         "prompt": "Review and polish this draft about: {task}", "depends_on": ["draft"]},
    ],
}


class ExecutionPlanner:
    """Analyzes tasks and produces optimized multi-step execution plans.

    Usage:
        planner = ExecutionPlanner()
        plan = planner.plan("Implement JWT auth in FastAPI")
        print(plan)  # Shows the multi-step plan
        results = planner.execute(plan)  # Runs each step
    """

    def __init__(self):
        self.scheduler = ModelScheduler()

    def plan(self, task: str, profile: str = "balanced") -> ExecutionPlan:
        """Analyze a task and produce an execution plan."""
        # 1. Classify the main task type
        task_type = self.scheduler.classify_task(task)

        # 2. Get the decomposition pattern
        pattern = TASK_PATTERNS.get(task_type, TASK_PATTERNS["coding"])
        if not pattern:
            pattern = TASK_PATTERNS["coding"]

        # 3. Build execution steps
        steps = []
        total_cost = 0.0

        for step_def in pattern:
            # Route this step to the best model and terminal
            route = self.scheduler.route(
                step_def["prompt"].format(task=task),
                step_def["task_type"],
                profile=profile,
            )
            terminal = best_terminal(step_def["task_type"], prefer_free=(profile == "free"))

            step = ExecutionStep(
                id=step_def["id"],
                description=step_def["description"],
                task_type=step_def["task_type"],
                model=route.model,
                terminal=terminal,
                provider=route.provider,
                estimated_cost=route.estimated_cost,
                depends_on=step_def.get("depends_on", []),
                prompt_template=step_def["prompt"],
            )
            total_cost += route.estimated_cost
            steps.append(step)

        return ExecutionPlan(
            task=task,
            steps=steps,
            total_estimated_cost=round(total_cost, 6),
            total_steps=len(steps),
        )

    def format_plan(self, plan: ExecutionPlan) -> str:
        """Format an execution plan as a human-readable string."""
        lines = [
            f"Execution Plan: {plan.task}",
            f"Estimated cost: ${plan.total_estimated_cost:.4f}",
            f"Steps: {plan.total_steps}",
            "",
        ]

        for i, step in enumerate(plan.steps, 1):
            cost_str = f"${step.estimated_cost:.4f}" if step.estimated_cost > 0 else "free"
            deps = f"  (after: {', '.join(step.depends_on)})" if step.depends_on else ""
            lines.append(f"  [{i}] {step.description}")
            lines.append(f"       {step.terminal:<12} → {step.model}")
            lines.append(f"       {step.task_type:<12} {cost_str}{deps}")
            lines.append("")

        return "\n".join(lines)

    def build_capability_graph(self, task: str, profile: str = "balanced") -> dict:
        """Build a capability graph for a task.

        Returns a structured graph showing capabilities, weights, and dependencies.
        """
        task_type = self.scheduler.classify_task(task)
        pattern = TASK_PATTERNS.get(task_type, TASK_PATTERNS["coding"])
        if not pattern:
            pattern = TASK_PATTERNS["coding"]

        graph = []
        for step_def in pattern:
            route = self.scheduler.route(
                step_def["prompt"].format(task=task),
                step_def["task_type"],
                profile=profile,
            )
            graph.append({
                "id": step_def["id"],
                "capability": step_def["task_type"],
                "description": step_def["description"],
                "model": route.model,
                "provider": route.provider,
                "cost_tier": route.cost_tier,
                "estimated_cost": route.estimated_cost,
                "depends_on": step_def.get("depends_on", []),
            })

        return {
            "task": task,
            "task_type": task_type,
            "profile": profile,
            "steps": graph,
            "total_steps": len(graph),
            "total_cost": round(sum(s["estimated_cost"] for s in graph), 6),
        }

    def format_graph(self, graph: dict) -> str:
        """Format a capability graph as a human-readable string."""
        lines = [
            f"Capability Graph: {graph['task']}",
            f"Type: {graph['task_type']}  Profile: {graph['profile']}",
            f"Estimated cost: ${graph['total_cost']:.4f}",
            f"Steps: {graph['total_steps']}",
            "",
        ]

        for i, step in enumerate(graph["steps"], 1):
            cost_str = f"${step['estimated_cost']:.4f}" if step['estimated_cost'] > 0 else "free"
            deps = f" → {', '.join(step['depends_on'])}" if step["depends_on"] else ""
            lines.append(f"  [{i}] {step['capability']:<12} {step['description']}")
            lines.append(f"       {step['model']:<32} {cost_str}{deps}")
            lines.append("")

        return "\n".join(lines)
