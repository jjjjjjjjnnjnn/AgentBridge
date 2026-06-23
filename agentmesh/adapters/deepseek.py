"""DeepSeek adapter (OpenAI-compatible API)."""
from __future__ import annotations

from agentmesh.adapters.base import AgentResponse, BaseAdapter


class DeepSeekAdapter(BaseAdapter):
    provider = "deepseek"
    default_model = "deepseek-chat"

    def _build_client(self):
        import httpx

        api_key = self.config.get("api_key") or ""
        base_url = self.config.get("base_url") or "https://api.deepseek.com/v1"
        return httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=120,
        )

    def chat(self, prompt: str, **kwargs) -> AgentResponse:
        return self.chat_with_context([{"role": "user", "content": prompt}], **kwargs)

    def chat_with_context(self, messages: list[dict], **kwargs) -> AgentResponse:
        client = self._build_client()
        body = {
            "model": kwargs.get("model") or self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.config.get("max_tokens", 4096)),
            "temperature": kwargs.get("temperature", self.config.get("temperature", 0.7)),
        }
        resp = client.post("/chat/completions", json=body)
        resp.raise_for_status()
        data = resp.json()
        choice = data["choices"][0]
        return AgentResponse(
            content=choice["message"]["content"],
            model=data["model"],
            provider=self.provider,
            usage=data.get("usage", {}),
            raw=data,
        )
