"""Any OpenAI-compatible chat completions endpoint.

Works with OpenAI, Azure OpenAI gateways, OpenRouter, Together, Groq, vLLM,
Ollama (`/v1`), LM Studio and other self-hosted open-source servers. The base
URL and model name come from the environment.
"""

import json
from collections.abc import AsyncIterator

import httpx

from app.ai.base import ChatMessage, ChatResult, ProviderRequestError

_TIMEOUT = httpx.Timeout(120.0, connect=10.0)


class OpenAICompatibleChatModel:
    def __init__(self, *, base_url: str, api_key: str, model: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.name = model

    @property
    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _payload(
        self,
        messages: list[ChatMessage],
        temperature: float,
        max_output_tokens: int,
        stream: bool,
    ) -> dict:
        return {
            "model": self.name,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_output_tokens,
            "stream": stream,
        }

    async def complete(
        self, messages: list[ChatMessage], *, temperature: float, max_output_tokens: int
    ) -> ChatResult:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=self._headers,
                json=self._payload(messages, temperature, max_output_tokens, False),
            )
        if response.status_code >= 400:
            raise ProviderRequestError(f"Provider error [{response.status_code}]: {response.text}")

        body = response.json()
        usage = body.get("usage") or {}
        return ChatResult(
            content=body["choices"][0]["message"]["content"],
            model=body.get("model", self.name),
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

    async def stream(
        self, messages: list[ChatMessage], *, temperature: float, max_output_tokens: int
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers=self._headers,
                json=self._payload(messages, temperature, max_output_tokens, True),
            ) as response:
                if response.status_code >= 400:
                    detail = (await response.aread()).decode("utf-8", "replace")
                    raise ProviderRequestError(
                        f"Provider error [{response.status_code}]: {detail}"
                    )
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = chunk.get("choices") or []
                    if not choices:
                        continue
                    piece = (choices[0].get("delta") or {}).get("content")
                    if piece:
                        yield piece
