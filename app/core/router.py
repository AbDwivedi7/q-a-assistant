import json
from typing import Optional
from .llm import call_router_llm, call_answer_llm
from ..tools.tool_registry import ToolRegistry
from ..models.schemas import RoutingDecision


class Router:
    def __init__(self, tools: ToolRegistry):
        self.tools = tools

    async def route_and_answer(self, user_text: str) -> tuple[str, Optional[str], float, float]:
        routing_json, model_latency = call_router_llm(user_text)

        if routing_json.get("type") == "tool":
            action = routing_json.get("action")
            tool_input = routing_json.get("input") or {}
            tool = self.tools.get(action)
            if not tool:
                # unknown tool: fall back to LLM answer
                answer, ans_lat = call_answer_llm(user_text)
                return answer, None, 0.0, ans_lat
            output = await tool.run(**tool_input)
            # Optional: ask LLM to clean up tool output in context
            final, ans_lat = call_answer_llm(
                f"User asked: {user_text}\nTool {action} returned: {output}.\nCompose a concise helpful answer."
            )
            return final, action, 0.0, ans_lat

        # direct answer path
        answer = routing_json.get("answer")
        if not answer:
            answer, _ = call_answer_llm(user_text)
        return answer, None, 0.0, model_latency