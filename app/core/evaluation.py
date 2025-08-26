from __future__ import annotations
import asyncio
from dataclasses import dataclass
from typing import Optional, Sequence
import yaml

from .llm import call_router_llm
from ..tools import ToolRegistry, WeatherTool, StocksTool
from .router import Router
from .memory import MemoryStore
from .context import ContextManager


@dataclass
class EvalResult:
    case_id: str
    question: str
    predicted_action: str
    expected_action: str | list[str]
    route_correct: bool
    used_tool: Optional[str] = None
    answer_contains: Optional[str] = None
    answer_correct: Optional[bool] = None
    router_raw: Optional[dict] = None


@dataclass
class EvalSummary:
    total: int
    route_accuracy: float
    answer_accuracy: Optional[float]


def _as_list(x: str | Sequence[str] | None) -> list[str]:
    if x is None:
        return []
    if isinstance(x, str):
        return [x]
    return list(x)


async def evaluate_router(yaml_path: str) -> list[EvalResult]:
    """Backward-compatible API: returns per-case results.
    Now also computes optional answer correctness if `expect_contains` is provided in a case.
    YAML case fields supported:
      - id: str
      - question: str
      - expect_action: str | [str, ...]  (e.g., "get_weather" or ["get_weather","get_forecast"])  // defaults to "none"
      - expect_contains: str  (substring expected in the final answer)
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)

    # Tools + router for full-path evaluation when needed
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(StocksTool())
    mem = MemoryStore()
    ctx = ContextManager(mem)
    router = Router(registry, mem, ctx)

    results: list[EvalResult] = []

    for case in cases:
        q: str = case["question"]
        case_id: str = case["id"]
        expected_any = _as_list(case.get("expect_action", "none")) or ["none"]
        expect_contains: Optional[str] = case.get("expect_contains")

        router_json, _ = call_router_llm(q)
        predicted_action = router_json.get("action") if router_json.get("type") == "tool" else "none"
        route_correct = predicted_action in expected_any

        used_tool = None
        answer_correct = None
        if expect_contains is not None:
            # Run full route (tool + polish) for answer-level check
            answer, used_tool, *_ = await router.route_and_answer("eval", q)
            answer_correct = (expect_contains.lower() in (answer or "").lower())

        results.append(
            EvalResult(
                case_id=case_id,
                question=q,
                predicted_action=predicted_action,
                expected_action=expected_any if len(expected_any) > 1 else expected_any[0],
                route_correct=route_correct,
                used_tool=used_tool,
                answer_contains=expect_contains,
                answer_correct=answer_correct,
                router_raw=router_json,
            )
        )

    return results


def summarize(results: list[EvalResult]) -> EvalSummary:
    total = len(results)
    route_hits = sum(1 for r in results if r.route_correct)
    route_acc = route_hits / total if total else 0.0
    # Only compute answer accuracy over cases that specified expect_contains
    answer_cases = [r for r in results if r.answer_correct is not None]
    ans_acc = (sum(1 for r in answer_cases if r.answer_correct) / len(answer_cases)) if answer_cases else None
    return EvalSummary(total=total, route_accuracy=route_acc, answer_accuracy=ans_acc)


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python -m app.core.evaluation <path/to/testcases.yaml>")
        sys.exit(1)

    path = sys.argv[1]

    async def _run():
        res = await evaluate_router(path)
        summary = summarize(res)
        # pretty print
        print("Per-case results:")
        for r in res:
            print(
                f"- [{r.case_id}] predicted={r.predicted_action} expected={r.expected_action} "
                f"route={'OK' if r.route_correct else 'MISS'}"
                + (f", used_tool={r.used_tool}" if r.used_tool else "")
                + (f", answer_contains='{r.answer_contains}' -> {'OK' if r.answer_correct else 'MISS'}" if r.answer_contains else "")
            )
        print("Summary:")
        print(f"  total: {summary.total}")
        print(f"  route_accuracy: {summary.route_accuracy:.3f}")
        if summary.answer_accuracy is not None:
            print(f"  answer_accuracy: {summary.answer_accuracy:.3f}")
        # Also emit JSON for CI pipelines
        print("JSON:" + json.dumps({
            "results": [r.__dict__ for r in res],
            "summary": summary.__dict__
        }, indent=2))

    asyncio.run(_run())