# app/core/context.py
from __future__ import annotations
import re
from typing import Optional
from .retrieval import SimpleIndexer
from .memory import MemoryStore

PRONOUNY_RE = re.compile(r"\b(?:there|here|that|those|them|it|same|again|previous|earlier)\b", re.I)

class ContextManager:
    def __init__(self, mem: MemoryStore):
        self.mem = mem
        self._idx_by_user: dict[str, SimpleIndexer] = {}

    def _idx(self, user_id: str) -> SimpleIndexer:
        if user_id not in self._idx_by_user:
            self._idx_by_user[user_id] = SimpleIndexer()
        return self._idx_by_user[user_id]

    def index_message(self, user_id: str, role: str, content: str):
        # keep a light semantic index per user (ephemeral in-memory)
        self._idx(user_id).add([f"{role}: {content}"])

    def mark_last_tool(self, user_id: str, tool: str):
        self.mem.set_kv(user_id, "meta", "last_tool", tool)

    def last_tool(self, user_id: str) -> Optional[str]:
        return self.mem.get_kv(user_id, "meta", "last_tool")

    def looks_followup(self, msg: str) -> bool:
        return bool(PRONOUNY_RE.search(msg or ""))

    def select_snippets(self, user_id: str, query: str, k: int = 2) -> list[str]:
        # semantic retrieval from prior turns
        try:
            return self._idx(user_id).search(query, k=k)
        except Exception:
            return []

    def resolve_tool_inputs(
        self,
        user_id: str,
        tool_name: str,
        tool_input: dict,
        input_schema: dict,
        user_msg: str,
    ) -> dict:
        """
        Generic slot backfill:
        - If a slot is missing and message looks like a follow-up, try scoped KV (tool_name, slot).
        - Otherwise leave blank and let the tool/LLM ask or fail gracefully.
        """
        out = dict(tool_input or {})
        followup = self.looks_followup(user_msg)
        for slot in input_schema.keys():
            if out.get(slot):
                continue
            if followup:
                val = self.mem.get_kv(user_id, tool_name, slot)
                if val:
                    out[slot] = val
        return out

    def persist_tool_memory(self, user_id: str, tool_name: str, tool_input: dict):
        # Save whatever slots were actually used so later follow-ups can reference them
        for k, v in (tool_input or {}).items():
            if isinstance(v, (str, int, float)) and str(v).strip():
                self.mem.set_kv(user_id, tool_name, k, str(v))
        self.mark_last_tool(user_id, tool_name)

    def should_include_history_for_polish(self, user_id: str, tool_name: str, msg: str) -> bool:
        # Only include snippets if this looks like a follow-up AND it’s the same tool namespace
        return self.looks_followup(msg) and (self.last_tool(user_id) == tool_name)
