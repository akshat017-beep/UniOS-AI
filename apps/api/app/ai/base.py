"""Provider-agnostic model interfaces.

Nothing in the application imports a vendor SDK directly. Swapping providers is
an environment-variable change, never a code change.
"""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant"]


@dataclass(slots=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(slots=True)
class ChatResult:
    content: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class ProviderNotConfiguredError(RuntimeError):
    """Raised when no AI provider credentials are present in the environment."""


class ProviderRequestError(RuntimeError):
    """Raised when the upstream provider returns an error."""


@runtime_checkable
class ChatModel(Protocol):
    name: str

    async def complete(
        self, messages: list[ChatMessage], *, temperature: float, max_output_tokens: int
    ) -> ChatResult: ...

    def stream(
        self, messages: list[ChatMessage], *, temperature: float, max_output_tokens: int
    ) -> AsyncIterator[str]: ...
