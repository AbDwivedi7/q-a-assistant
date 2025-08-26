from __future__ import annotations
from typing import Protocol, Any


class Tool(Protocol):
    name: str
    description: str
    input_schema: dict

    async def run(self, **kwargs) -> str:  # returns human-readable answer
        ...


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_descriptions(self) -> str:
        return "\n".join(
            f"- {t.name}: {t.description} input={t.input_schema}" for t in self._tools.values()
        )