from __future__ import annotations
import asyncio
import time
import yaml
from dataclasses import dataclass
from typing import Optional
from .llm import call_router_llm, call_answer_llm
from ..tools import ToolRegistry, WeatherTool, StocksTool


@dataclass
class EvalResult:
    case_id: str
    predicted: str
    expected: str
    correct: bool


async def evaluate_router(yaml_path: str) -> list[EvalResult]:
    with open(yaml_path, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)

    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(StocksTool())

    results: list[EvalResult] = []
    for case in cases:
        q = case["question"]
        expected = case.get("expect_action", "none")
        routing_json, _ = call_router_llm(q)
        predicted = routing_json.get("action") if routing_json.get("type") == "tool" else "none"
        results.append(EvalResult(case_id=case["id"], predicted=predicted, expected=expected, correct=(predicted == expected)))
    return results