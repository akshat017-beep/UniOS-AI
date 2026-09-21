"""Provider-agnostic embeddings.

Any OpenAI-compatible `/embeddings` endpoint works (OpenAI, Together, vLLM,
Ollama, LM Studio, text-embeddings-inference). No vendor SDK is imported.
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol, runtime_checkable

import httpx

from app.ai.base import ProviderNotConfiguredError, ProviderRequestError
from app.core.config import settings


@runtime_checkable
class EmbeddingModel(Protocol):
    name: str
    dimensions: int

    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAICompatibleEmbeddingModel:
    def __init__(self, *, base_url: str, api_key: str, model: str, dimensions: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.name = model
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"model": self.name, "input": texts}
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    f"{self.base_url}/embeddings", json=payload, headers=headers
                )
        except httpx.HTTPError as exc:
            raise ProviderRequestError(f"Embedding provider unreachable: {exc}") from exc
        if response.status_code >= 400:
            raise ProviderRequestError(
                f"Embedding provider returned {response.status_code}: {response.text[:300]}"
            )
        data = response.json().get("data", [])
        return [item["embedding"] for item in data]


class HashingEmbeddingModel:
    """Deterministic local fallback used for tests and offline development.

    It is NOT semantic. It is only enabled when EMBEDDING_PROVIDER=hashing, and the
    API reports retrieval quality as 'lexical fallback' so nothing is overstated.
    """

    def __init__(self, dimensions: int = 256) -> None:
        self.name = "hashing-local"
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return [value / norm for value in vector] if norm else vector


def get_embedding_model() -> EmbeddingModel:
    provider = settings.embedding_provider.strip().lower()
    if provider == "hashing":
        return HashingEmbeddingModel(settings.embedding_dimensions)
    if provider != "openai_compatible":
        raise ProviderNotConfiguredError(
            f"Unknown EMBEDDING_PROVIDER '{settings.embedding_provider}'. "
            "Supported: openai_compatible, hashing."
        )
    base_url = settings.embedding_base_url or settings.ai_base_url
    api_key = settings.embedding_api_key or settings.ai_api_key
    if not base_url or not settings.embedding_model:
        raise ProviderNotConfiguredError(
            "Embeddings are not configured. Set EMBEDDING_BASE_URL (or AI_BASE_URL) and "
            "EMBEDDING_MODEL, or set EMBEDDING_PROVIDER=hashing for offline development."
        )
    if not api_key and not settings.ai_allow_keyless:
        raise ProviderNotConfiguredError(
            "EMBEDDING_API_KEY is missing. Set it, or AI_ALLOW_KEYLESS=true for a local server."
        )
    return OpenAICompatibleEmbeddingModel(
        base_url=base_url,
        api_key=api_key,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
    )


def embeddings_are_configured() -> bool:
    try:
        get_embedding_model()
    except ProviderNotConfiguredError:
        return False
    return True
