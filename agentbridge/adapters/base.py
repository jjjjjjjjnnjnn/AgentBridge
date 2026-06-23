"""Base agent adapter interface."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


class AdapterError(RuntimeError):
    """Agent adapter error with context."""


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
    env_key: str = ""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._warn_if_missing_key()

    def _warn_if_missing_key(self):
        if not self.env_key:
            return
        api_key = self.config.get("api_key") or ""
        if not api_key:
            import os
            if not os.environ.get(self.env_key):
                logger.warning(
                    f"No API key for {self.provider}. "
                    f"Set {self.env_key} env var or configure in config."
                )

    def _get_api_key(self) -> str | None:
        key = self.config.get("api_key") or ""
        if key:
            return key
        if self.env_key:
            import os
            return os.environ.get(self.env_key)
        return None

    @abstractmethod
    def chat(self, prompt: str, **kwargs) -> AgentResponse:
        ...

    @abstractmethod
    def chat_with_context(self, messages: list[dict], **kwargs) -> AgentResponse:
        ...

    @property
    def model(self) -> str:
        return self.config.get("model") or self.default_model
