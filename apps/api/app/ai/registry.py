"""Resolve the configured chat model. One place decides which provider is used."""

from functools import lru_cache

from app.ai.base import ChatModel, ProviderNotConfiguredError
from app.ai.providers.openai_compatible import OpenAICompatibleChatModel
from app.core.config import settings

_SUPPORTED = {"openai_compatible"}


@lru_cache
def get_chat_model() -> ChatModel:
    provider = settings.ai_provider.strip().lower()
    if provider not in _SUPPORTED:
        raise ProviderNotConfiguredError(
            f"Unknown AI_PROVIDER '{settings.ai_provider}'. Supported: {', '.join(_SUPPORTED)}."
        )
    if not settings.ai_base_url or not settings.ai_model:
        raise ProviderNotConfiguredError(
            "The AI provider is not configured. Set AI_BASE_URL, AI_MODEL and (for hosted "
            "providers) AI_API_KEY in the environment, then restart the API."
        )
    if not settings.ai_api_key and not settings.ai_allow_keyless:
        raise ProviderNotConfiguredError(
            "AI_API_KEY is missing. Set it, or set AI_ALLOW_KEYLESS=true for a local "
            "open-source server such as Ollama or vLLM that needs no key."
        )
    return OpenAICompatibleChatModel(
        base_url=settings.ai_base_url,
        api_key=settings.ai_api_key,
        model=settings.ai_model,
    )


def ai_is_configured() -> bool:
    try:
        get_chat_model()
    except ProviderNotConfiguredError:
        return False
    return True
