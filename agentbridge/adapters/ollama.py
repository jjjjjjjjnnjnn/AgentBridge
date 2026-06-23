"""Ollama local model adapter."""
from __future__ import annotations

import httpx

from agentbridge.adapters.base import AdapterError, AgentResponse, BaseAdapter


class OllamaAdapter(BaseAdapter):
    provider = "ollama"
    default_model = "qwen2.5:7b"
    env_key = ""

    def _build_client(self):
        base_url = self.config.get("base_url", "http://localhost:11434")
        return httpx.Client(base_url=base_url, timeout=300)

    def chat(self, prompt: str, **kwargs) -> AgentResponse:
        return self.chat_with_context([{"role": "user", "content": prompt}], **kwargs)

    def chat_with_context(self, messages: list[dict], **kwargs) -> AgentResponse:
        client = self._build_client()
        body = {
            "model": kwargs.get("model") or self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": kwargs.get("max_tokens", self.config.get("max_tokens", 4096)),
                "temperature": kwargs.get("temperature", self.config.get("temperature", 0.7)),
            },
        }
        try:
            resp = client.post("/api/chat", json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:300] if e.response else str(e)
            raise AdapterError(f"{self.provider} API error {e.response.status_code}: {detail}")
        except httpx.RequestError as e:
            raise AdapterError(f"Connection to {self.provider} failed: {e}")

        data = resp.json()
        msg = data.get("message")
        if not msg:
            raise AdapterError(f"{self.provider} returned unexpected response: missing 'message' field")
        return AgentResponse(
            content=msg.get("content", ""),
            model=data.get("model", self.model),
            provider=self.provider,
            usage={"total_duration": data.get("total_duration", 0)},
            raw=data,
        )
