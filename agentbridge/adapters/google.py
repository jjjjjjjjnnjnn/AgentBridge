"""Google Gemini adapter."""
from __future__ import annotations

from urllib.parse import quote

import httpx

from agentbridge.adapters.base import AdapterError, AgentResponse, BaseAdapter


class GoogleAdapter(BaseAdapter):
    provider = "google"
    default_model = "gemini-2.5-flash"
    env_key = "GEMINI_API_KEY"

    def _build_client(self):
        api_key = self._get_api_key()
        if not api_key:
            raise AdapterError(f"Missing API key. Set {self.env_key} env var or configure in config.")
        return httpx.Client(
            headers={"Content-Type": "application/json"},
            timeout=120,
            params={"key": api_key},
        )

    def chat(self, prompt: str, **kwargs) -> AgentResponse:
        return self.chat_with_context([{"role": "user", "content": prompt}], **kwargs)

    def chat_with_context(self, messages: list[dict], **kwargs) -> AgentResponse:
        client = self._build_client()
        model = kwargs.get("model") or self.model

        gemini_contents = []
        for m in messages:
            if m["role"] == "system":
                gemini_contents.insert(0, {"role": "user", "parts": [{"text": f"[System] {m['content']}"}]})
            elif m["role"] == "user":
                gemini_contents.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                gemini_contents.append({"role": "model", "parts": [{"text": m["content"]}]})

        body = {
            "contents": gemini_contents,
            "generationConfig": {
                "maxOutputTokens": kwargs.get("max_tokens", self.config.get("max_tokens", 4096)),
                "temperature": kwargs.get("temperature", self.config.get("temperature", 0.7)),
            },
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{quote(model)}:generateContent"

        try:
            resp = client.post(url, json=body)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:300] if e.response else str(e)
            raise AdapterError(f"{self.provider} API error {e.response.status_code}: {detail}")
        except httpx.RequestError as e:
            raise AdapterError(f"Connection to {self.provider} failed: {e}")

        data = resp.json()
        text = ""
        candidates = data.get("candidates", [])
        if candidates:
            for part in candidates[0].get("content", {}).get("parts", []):
                text += part.get("text", "")
        return AgentResponse(
            content=text,
            model=model,
            provider=self.provider,
            usage=data.get("usageMetadata", {}),
            raw=data,
        )
