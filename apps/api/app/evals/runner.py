"""Run the internal evaluation suites.

    python -m app.evals.runner            # routing only (no provider needed)
    python -m app.evals.runner --answers  # also run answer quality checks

Answer checks require a configured provider; without one the runner says they were
skipped. It never reports a pass for a check it did not actually run.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass

from app.agents.registry import get_agent
from app.agents.router import route
from app.ai.base import ProviderNotConfiguredError, ProviderRequestError
from app.evals.cases import ANSWER_CASES, ROUTING_CASES
from app.services.generation import generate


@dataclass
class Result:
    suite: str
    name: str
    passed: bool
    detail: str = ""


def run_routing() -> list[Result]:
    results: list[Result] = []
    for case in ROUTING_CASES:
        decision = route(case.message)
        passed = decision.agent.name == case.expected_agent
        results.append(
            Result(
                suite="routing",
                name=case.message[:60],
                passed=passed,
                detail=f"expected {case.expected_agent}, got {decision.agent.name} "
                f"(confidence {decision.confidence:.2f})",
            )
        )
    return results


async def run_answers() -> list[Result]:
    results: list[Result] = []
    for case in ANSWER_CASES:
        try:
            text, _ = await generate(
                agent_name=case.agent,
                instruction=get_agent(case.agent).instructions,
                content=case.prompt,
            )
        except ProviderNotConfiguredError as exc:
            return [Result(suite="answers", name="skipped", passed=False, detail=str(exc))]
        except ProviderRequestError as exc:
            results.append(Result("answers", case.name, False, f"provider error: {exc}"))
            continue

        lowered = text.lower()
        missing = [term for term in case.must_include if term.lower() not in lowered]
        leaked = [term for term in case.must_not_include if term.lower() in lowered]
        results.append(
            Result(
                suite="answers",
                name=case.name,
                passed=not missing and not leaked,
                detail=f"missing={missing} leaked={leaked}",
            )
        )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="UniOS AI evaluation runner")
    parser.add_argument("--answers", action="store_true", help="also run answer-quality checks")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args()

    results = run_routing()
    if args.answers:
        results.extend(asyncio.run(run_answers()))

    if args.json:
        print(json.dumps([asdict(result) for result in results], indent=2))
    else:
        for result in results:
            mark = "PASS" if result.passed else "FAIL"
            print(f"[{mark}] {result.suite}: {result.name} — {result.detail}")
        failed = sum(1 for result in results if not result.passed)
        print(f"\n{len(results) - failed}/{len(results)} checks passed")

    return 1 if any(not result.passed for result in results if result.suite == "routing") else 0


if __name__ == "__main__":
    sys.exit(main())
