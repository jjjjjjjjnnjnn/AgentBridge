"""Terminal registry — discover and create terminal instances."""
from __future__ import annotations

from relayos.terminals.base import BaseTerminal
from relayos.terminals.adapters import (
    AiderTerminal,
    ChatgptCliTerminal,
    ClaudeCodeTerminal,
    CodexTerminal,
    ContinueTerminal,
    CopilotExtTerminal,
    CursorTerminal,
    CustomTerminal,
    FabricTerminal,
    GeminiCliTerminal,
    GitHubCopilotTerminal,
    HuggingFaceTerminal,
    KimiTerminal,
    LlmCliTerminal,
    MimoCodeTerminal,
    OpenClawTerminal,
    OpenCodeTerminal,
    OpenInterpreterTerminal,
    PiTerminal,
    QCodeTerminal,
    SgptTerminal,
)

REGISTRY: dict[str, type[BaseTerminal]] = {
    "claude": ClaudeCodeTerminal,
    "mimo": MimoCodeTerminal,
    "opencode": OpenCodeTerminal,
    "codex": CodexTerminal,
    "qcode": QCodeTerminal,
    "pi": PiTerminal,
    "cursor": CursorTerminal,
    "openclaw": OpenClawTerminal,
    "continue": ContinueTerminal,
    "copilot": GitHubCopilotTerminal,
    "huggingface": HuggingFaceTerminal,
    "gemini": GeminiCliTerminal,
    "aider": AiderTerminal,
    "interpreter": OpenInterpreterTerminal,
    "fabric": FabricTerminal,
    "sgpt": SgptTerminal,
    "chatgpt": ChatgptCliTerminal,
    "llm": LlmCliTerminal,
    "kimi": KimiTerminal,
    "copilot-ext": CopilotExtTerminal,
    "custom": CustomTerminal,
}


def get_terminal_class(type_name: str) -> type[BaseTerminal]:
    cls = REGISTRY.get(type_name)
    if not cls:
        available = ", ".join(sorted(REGISTRY))
        raise ValueError(f"Unknown terminal type '{type_name}'. Available: {available}")
    return cls


def register_terminal(type_name: str, cls: type[BaseTerminal]):
    REGISTRY[type_name] = cls


def list_terminal_types() -> list[dict]:
    """List all available terminal types with their status."""
    results = []
    for name, cls in REGISTRY.items():
        inst = cls()
        results.append({
            "type": name,
            "binary": getattr(inst, "binary", ""),
            "default_model": getattr(inst, "default_model", ""),
            "available": inst.check_available(),
        })
    return results
