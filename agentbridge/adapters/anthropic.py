"""Anthropic Claude adapter."""
from __future__ import annotations

import httpx

from agentbridge.adapters.base import AdapterError, AgentResponse, BaseAdapter


class AnthropicAdapter(BaseAdapter):
    provider = "anthropic"
    default_model = "claude-sonnet-4-20250514"
    env_key = "ANTHROPIC_API_KEY"

    def _build_client(self):
        api_key = self._get_api_key()
        if not api_key:
            raise AdapterError(f"Missing API key. Set {self.env_key} env var or configure in config.")
        base_url = self.config.get("base_url") or "https://api.anthropic.com/v1"
        return httpx.Client(
            base_url=base_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            timeout=120,
        )

    def chat(self, prompt: str, **kwargs) -> AgentResponse:
        return self.chat_with_context([{"role": "user", "content": prompt}], **kwargs)

    def chat_with_context(self, messages: list[dict], **kwargs) -> AgentResponse:
        client = self._build_client()
        system_parts = []
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system_parts.append(m["content"])
            else:
                filtered.append(m)

        body = {
            "model": kwargs.get("model") or self.model,
            "messages": filtered,
            "max_tokens": kwargs.get("max_tokens", self.config.get("max_tokens", 4096)),
            "temperature": kwargs.get("temperature", self.config.get("temperature", 0.7)),
        }
        if system_parts:
            body["system"] = "\n\n".join(system_parts)

        try:
            resp = client.post("/messages", json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:300] if e.response else str(e)
            raise AdapterError(f"{self.provider} API error {e.response.status_code}: {detail}")
        except httpx.RequestError as e:
            raise AdapterError(f"Connection to {self.provider} failed: {e}")

        data = resp.json()
        if "error" in data:
            raise AdapterError(f"{self.provider} API error: {data['error']}")
        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        return AgentResponse(
            content=text,
            model=data.get("model", self.model),
            provider=self.provider,
            usage={
                "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                "output_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
            raw=data,
        )
