"""The routing evaluation suite runs in CI; answer quality needs a provider."""

from app.evals.runner import run_routing


def test_routing_suite_passes() -> None:
    results = run_routing()
    failures = [result for result in results if not result.passed]
    assert not failures, "\n".join(f"{r.name}: {r.detail}" for r in failures)


def test_every_case_is_reported() -> None:
    assert len(run_routing()) >= 9
