import pytest

from app.agents.router import route


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("Explain binary search trees and give me MCQs", "study"),
        ("Summarise recent papers on transformer methodology", "research"),
        ("My python function throws a segmentation fault, debug it", "coding"),
        ("Review my resume for a backend internship", "career"),
        ("What are the library timings on campus?", "campus"),
        ("Calculate my CGPA from these SGPA values", "performance"),
        ("Draft an email to my professor asking for leave", "communication"),
        ("Write an announcement about the scholarship policy", "admin"),
    ],
)
def test_router_picks_the_right_agent(message: str, expected: str) -> None:
    assert route(message).agent.name == expected


def test_document_context_always_wins() -> None:
    decision = route("Explain this", has_document_context=True)
    assert decision.agent.name == "document"
    assert decision.confidence == 1.0


def test_unclear_message_falls_back_without_confidence() -> None:
    decision = route("hello there")
    assert decision.agent.name == "study"
    assert not decision.is_confident


def test_code_in_message_is_a_signal() -> None:
    decision = route("What does this do?\n```\ndef f(x):\n    return x\n```")
    assert decision.agent.name == "coding"
