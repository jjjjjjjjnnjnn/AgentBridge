"""DeepSeek adapter (OpenAI-compatible API)."""
from __future__ import annotations

import httpx

from agentbridge.adapters.base import AdapterError, AgentResponse, BaseAdapter


class DeepSeekAdapter(BaseAdapter):
    provider = "deepseek"
    default_model = "deepseek-chat"
    env_key = "DEEPSEEK_API_KEY"

    def _build_client(self):
        api_key = self._get_api_key()
        if not api_key:
            raise AdapterError(f"Missing API key. Set {self.env_key} env var or configure in config.")
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
        try:
            resp = client.post("/chat/completions", json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:300] if e.response else str(e)
            raise AdapterError(f"{self.provider} API error {e.response.status_code}: {detail}")
        except httpx.RequestError as e:
            raise AdapterError(f"Connection to {self.provider} failed: {e}")

        data = resp.json()
        choices = data.get("choices", [])
        if not choices:
            err = data.get("error", {}).get("message", "empty choices array")
            raise AdapterError(f"{self.provider} returned no choices: {err}")
        choice = choices[0]
        content = (choice.get("message") or {}).get("content") or ""
        return AgentResponse(
            content=content,
            model=data.get("model", self.model),
            provider=self.provider,
            usage=data.get("usage", {}),
            raw=data,
        )
