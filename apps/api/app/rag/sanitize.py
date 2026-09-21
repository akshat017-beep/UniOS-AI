"""Prompt-injection defence for retrieved content.

Retrieved text is DATA. It is fenced, labelled and scanned for instruction-like
patterns so the model (and the user) can see when a document tries to give orders.
"""

import re

_INJECTION_PATTERNS = (
    r"ignore (all |any |the )?(previous|prior|above) instructions",
    r"disregard (all |any |the )?(previous|prior|above)",
    r"you are now\b",
    r"system prompt",
    r"reveal (your|the) (prompt|instructions|rules)",
    r"act as (an? )?(admin|administrator|developer|root)",
    r"forget (everything|all previous)",
    r"</?(system|assistant)>",
)

_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in _INJECTION_PATTERNS]


def detect_injection(text: str) -> list[str]:
    """Return the suspicious phrases found in untrusted content."""
    found: list[str] = []
    for pattern in _COMPILED:
        match = pattern.search(text)
        if match:
            found.append(match.group(0).strip())
    return found


def fence(text: str) -> str:
    """Neutralise fence breakouts so retrieved text cannot escape its block."""
    return text.replace("```", "``\u200b`").strip()
