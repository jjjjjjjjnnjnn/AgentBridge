"""Base agent adapter interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentResponse:
    content: str
    model: str
    provider: str
    usage: dict = field(default_factory=dict)
    raw: Any = None


class BaseAdapter(ABC):
    """Every agent adapter must implement this interface."""

    provider: str = ""
    default_model: str = ""

    def __init__(self, config: dict | None = None):
        self.config = config or {}

    @abstractmethod
    def chat(self, prompt: str, **kwargs) -> AgentResponse:
        """Send a prompt and return the response."""
        ...

    @abstractmethod
    def chat_with_context(self, messages: list[dict], **kwargs) -> AgentResponse:
        """Send a message history and return the response."""
        ...

    @property
    def model(self) -> str:
        return self.config.get("model") or self.default_model
