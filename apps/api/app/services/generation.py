"""Single-shot generation helpers used by the workspaces (study, research, career).

Every helper goes through the same provider-agnostic chat model as the assistant,
so nothing here hard-codes a vendor or silently invents content when the provider
is not configured — the caller surfaces a 503 with the variables to set.
"""

from __future__ import annotations

from app.agents.registry import get_agent
from app.ai.base import ChatMessage
from app.ai.registry import get_chat_model
from app.core.config import settings


async def generate(
    *, agent_name: str, instruction: str, content: str, context: str = ""
) -> tuple[str, str]:
    """Return (text, model_name)."""
    agent = get_agent(agent_name)
    messages = [ChatMessage("system", agent.system_prompt), ChatMessage("system", instruction)]
    if context:
        messages.append(ChatMessage("system", context))
    messages.append(ChatMessage("user", content))

    model = get_chat_model()
    result = await model.complete(
        messages,
        temperature=settings.ai_temperature,
        max_output_tokens=settings.ai_max_output_tokens,
    )
    return result.content, result.model


STUDY_FORMATS = {
    "summary": "Produce a tight revision summary: key ideas, definitions, formulas, common traps.",
    "notes": "Produce structured study notes with headings, bullet points and worked examples.",
    "flashcards": (
        "Produce 10-15 flashcards as a markdown table with columns Question and Answer. "
        "One fact per card."
    ),
    "quiz": (
        "Produce 10 multiple-choice questions with four options each, then an answer key "
        "with one-line explanations."
    ),
    "plan": (
        "Produce a day-by-day study plan with time estimates and checkpoints for the "
        "period the student mentions (assume 7 days if unspecified)."
    ),
}

RESEARCH_FORMATS = {
    "outline": "Draft a paper outline: problem, related work themes, method, evaluation, threats.",
    "literature": (
        "Summarise the topic's research landscape by theme. Never invent citations — "
        "describe the kind of source needed where you cannot name a real one."
    ),
    "gaps": "Identify open research gaps and concrete next experiments, ranked by feasibility.",
    "critique": "Critique the supplied text: claims, evidence, method weaknesses, clarity.",
}
