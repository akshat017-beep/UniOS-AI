"""Intent detection and agent routing.

Deterministic keyword-and-signal scoring: fast, free, testable and explainable.
It returns the confidence and the matched signals so the UI can show why a given
agent answered, and so a model-based re-ranker can be layered on later without
changing any caller.
"""

import re
from dataclasses import dataclass

from app.agents.registry import AGENTS, DEFAULT_AGENT, Agent, get_agent

_CODE_BLOCK = re.compile(r"```|def |class |#include|console\.log|SELECT .* FROM", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    agent: Agent
    confidence: float
    signals: tuple[str, ...]

    @property
    def is_confident(self) -> bool:
        return self.confidence >= 0.4


def route(message: str, *, has_document_context: bool = False) -> RoutingDecision:
    text = message.lower()

    if has_document_context:
        return RoutingDecision(get_agent("document"), 1.0, ("attached document",))

    scores: dict[str, list[str]] = {name: [] for name in AGENTS}
    for name, agent in AGENTS.items():
        for keyword in agent.keywords:
            if keyword in text:
                scores[name].append(keyword)

    if _CODE_BLOCK.search(message):
        scores["coding"].append("code in message")

    best = max(scores, key=lambda name: len(scores[name]))
    matched = tuple(scores[best])
    if not matched:
        return RoutingDecision(get_agent(DEFAULT_AGENT), 0.0, ())

    confidence = min(1.0, 0.4 + 0.2 * (len(matched) - 1))
    return RoutingDecision(get_agent(best), confidence, matched)
