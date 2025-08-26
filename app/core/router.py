# app/core/router.py
from typing import Optional
from .llm import call_router_llm, call_answer_llm
from ..tools.tool_registry import ToolRegistry
from ..models.schemas import RoutingDecision
from .context import ContextManager

class Router:
    def __init__(self, tools: ToolRegistry, mem, ctx: ContextManager):
        self.tools = tools
        self.mem = mem
        self.ctx = ctx

    async def route_and_answer(self, user_id: str, user_text: str) -> tuple[str, Optional[str], float, float]:
        routing_json, model_latency = call_router_llm(user_text)

        if routing_json.get("type") == "tool":
            action = routing_json.get("action")
            tool_input = (routing_json.get("input") or {}).copy()
            tool = self.tools.get(action)
            if not tool:
                answer, ans_lat = call_answer_llm(user_text)
                return answer, None, 0.0, ans_lat

            # dynamic, generic backfill using the tool's declared schema
            tool_input = self.ctx.resolve_tool_inputs(
                user_id=user_id,
                tool_name=action,
                tool_input=tool_input,
                input_schema=getattr(tool, "input_schema", {}) or {},
                user_msg=user_text,
            )

            raw = await tool.run(**tool_input)
            self.ctx.persist_tool_memory(user_id, action, tool_input)

            # minimal, guarded polish; optionally add 1–2 relevant snippets
            snippets = []
            if self.ctx.should_include_history_for_polish(user_id, action, user_text):
                snippets = self.ctx.select_snippets(user_id, user_text, k=2)

            guard = (
                "Answer ONLY the user's question using the tool result. "
                "Do not add unrelated information."
            )
            snippet_block = ("\nRelevant prior context:\n" + "\n".join(snippets)) if snippets else ""
            final, ans_lat = call_answer_llm(
                f"User asked: {user_text}\nTool {action} returned: {raw}.{snippet_block}\n{guard}"
            )
            return final, action, 0.0, ans_lat

        # LLM-only path: include at most top-2 relevant snippets, not full history
        snippets = self.ctx.select_snippets(user_id, user_text, k=2)
        context = ("\nRelevant prior context:\n" + "\n".join(snippets)) if snippets else ""
        prompt = (user_text + context) if context else user_text
        answer, ans_lat = call_answer_llm(prompt)
        return answer, None, 0.0, ans_lat