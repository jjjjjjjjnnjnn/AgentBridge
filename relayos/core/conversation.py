"""Conversation Engine — manages sessions, routes messages to workers.

The engine is the runtime that powers all interaction modes:
- relay chat <worker>: single-worker conversation
- relay ask <task>: auto session with task decomposition
- relay group <name>: multi-worker collab session
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from relayos.adapters import get_adapter
from relayos.config import load_config
from relayos.core.planner import ExecutionPlanner
from relayos.core.scheduler import ModelScheduler
from relayos.core.session import SessionStore, SessionMessage
from relayos.core.state import StateStore
from relayos.core.worker import WorkerManager

logger = logging.getLogger(__name__)


class ConversationEngine:
    """Core engine for all session-based AI interactions.

    Routes user input through the session pipeline:
    user → session → router → worker(s) → model(s) → result
    """

    def __init__(self):
        self.sessions = SessionStore()
        self.state = StateStore()
        self.workers = WorkerManager()
        self.scheduler = ModelScheduler()
        self.planner = ExecutionPlanner()
        self.config = load_config()

    # ── Chat (single worker / auto-routed) ─────────────────

    def chat(self, message: str, worker_name: Optional[str] = None,
             session_id: Optional[str] = None, profile: str = "") -> dict:
        """Send a message to a worker (or auto-routed).

        Returns the response with session context.
        """
        # Get or create session
        session = None
        if session_id:
            session = self.sessions.get_session(session_id)
        if not session:
            name = f"chat-{worker_name or 'auto'}"
            participants = [worker_name] if worker_name else []
            session = self.sessions.create_session(name, "chat", participants, profile or "balanced")

        # Store user message
        self.sessions.add_message(session.id, "user", "user", message, "message")

        # Detect capability from message content
        capability = self.scheduler.classify_task(message)
        strategy = session.last_strategy or session.profile

        # Use last capability to inform routing, not last model
        route = self.scheduler.route(message, capability, profile=strategy or session.profile)
        target = worker_name or route.provider

        # Get worker or create temporary
        worker = self.workers.get(target)
        if not worker:
            route = self.scheduler.route(message, profile=session.profile)
            try:
                adapter = get_adapter(route.provider, {
                    "api_key": self.config.resolve_api_key(route.provider),
                    "model": route.model,
                })
                response = adapter.chat(message)
                result = response.content
                model_used = response.model
                tokens = sum(response.usage.values()) if response.usage else 0
            except Exception as e:
                result = f"[Error] {e}"
                model_used = route.model
                tokens = 0
        else:
            result = self.workers.run(target, message)
            model_used = worker.model
            tokens = 0

        # Store assistant message
        self.sessions.add_message(
            session.id, "assistant", target, result,
            "result", model_used, tokens,
        )

        # Remember capability + strategy (not hard-bound to one model)
        self.sessions.set_last_used(session.id, target, model_used, capability, strategy)

        return {
            "session_id": session.id,
            "worker": target,
            "model": model_used,
            "content": result,
            "tokens": tokens,
        }

    # ── Ask (auto task decomposition + execution) ─────────

    def ask(self, task: str, profile: str = "balanced") -> dict:
        """Submit a task: auto-decompose, execute, return results."""
        session = self.sessions.create_session(task[:40], "ask", profile=profile)

        # Store task
        self.sessions.add_message(session.id, "user", "user", task, "task")

        # Generate capability graph
        graph = self.planner.build_capability_graph(task, profile)
        self.sessions.set_last_used(session.id, capability=graph["task_type"], strategy=profile)

        # Plan execution
        plan = self.planner.plan(task, profile)
        results = []

        for step in plan.steps:
            prompt = step.prompt_template.format(task=task)
            self.sessions.add_message(
                session.id, "system", step.terminal,
                f"Starting: {step.description}", "task",
                step.model,
            )

            try:
                adapter = get_adapter(step.provider, {
                    "api_key": self.config.resolve_api_key(step.provider),
                    "model": step.model,
                })
                response = adapter.chat(prompt)
                step.status = "done"

                self.sessions.add_message(
                    session.id, "assistant", step.terminal,
                    response.content[:500], "result",
                    response.model,
                    sum(response.usage.values()) if response.usage else 0,
                )
                results.append({
                    "step": step.id,
                    "worker": step.terminal,
                    "model": response.model,
                    "content": response.content[:500],
                })
            except Exception as e:
                step.status = "error"
                self.sessions.add_message(
                    session.id, "system", step.terminal,
                    f"Error: {e}", "result",
                )

        return {
            "session_id": session.id,
            "profile": profile,
            "steps": len(plan.steps),
            "results": results,
        }

    # ── Group (multi-worker collaboration) ─────────────────

    def group_chat(self, message: str, session_id: Optional[str] = None,
                   participants: Optional[list[str]] = None,
                   profile: str = "balanced") -> dict:
        """Send a message to a group of workers.

        Each participant responds in sequence (event-driven, not parallel chat).
        """
        session = None
        if session_id:
            session = self.sessions.get_session(session_id)
        if not session:
            parts = participants or ["researcher", "architect", "coder", "reviewer"]
            session = self.sessions.create_session("group", "group", parts, profile)

        self.sessions.add_message(session.id, "user", "user", message, "task")

        responses = []
        for worker_name in session.participants:
            try:
                # Give each worker context of previous responses
                context = f"Task: {message}\n\nPrevious responses:\n"
                for r in responses:
                    context += f"\n{r['worker']}: {r['content'][:200]}"
                context += f"\n\nNow you ({worker_name}) respond:"

                adapter = get_adapter(worker_name, {
                    "api_key": self.config.resolve_api_key(worker_name),
                })
                response = adapter.chat(context)

                self.sessions.add_message(
                    session.id, "assistant", worker_name,
                    response.content[:500], "finding",
                    response.model,
                    sum(response.usage.values()) if response.usage else 0,
                )
                responses.append({
                    "worker": worker_name,
                    "model": response.model,
                    "content": response.content[:500],
                })
            except Exception as e:
                logger.warning(f"Group chat: {worker_name} failed: {e}")
                responses.append({"worker": worker_name, "error": str(e)})

        return {
            "session_id": session.id,
            "participants": session.participants,
            "responses": responses,
        }

    # ── Session Utilities ──────────────────────────────────

    def get_timeline(self, session_id: str, limit: int = 20) -> list[dict]:
        """Get formatted session timeline for UI."""
        return self.sessions.get_timeline(session_id, limit)

    def list_sessions(self, limit: int = 10) -> list[dict]:
        """List all recent sessions."""
        return self.sessions.list_sessions(limit)

    def plan_capability(self, task: str, profile: str = "balanced") -> dict:
        """Generate a capability graph for a task without executing."""
        graph = self.planner.build_capability_graph(task, profile)
        return graph
