"""Anthropic Claude adapter."""
from __future__ import annotations

from agentmesh.adapters.base import AgentResponse, BaseAdapter


class AnthropicAdapter(BaseAdapter):
    provider = "anthropic"
    default_model = "claude-sonnet-4-20250514"

    def _build_client(self):
        import httpx

        api_key = self.config.get("api_key") or ""
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
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system += m["content"] + "\n"
            else:
                filtered.append(m)

        body = {
            "model": kwargs.get("model") or self.model,
            "messages": filtered,
            "max_tokens": kwargs.get("max_tokens", self.config.get("max_tokens", 4096)),
            "temperature": kwargs.get("temperature", self.config.get("temperature", 0.7)),
        }
        if system.strip():
            body["system"] = system.strip()

        resp = client.post("/messages", json=body)
        resp.raise_for_status()
        data = resp.json()
        content_blocks = data.get("content", [])
        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        return AgentResponse(
            content=text,
            model=data["model"],
            provider=self.provider,
            usage={
                "input_tokens": data.get("usage", {}).get("input_tokens", 0),
                "output_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
            raw=data,
        )
