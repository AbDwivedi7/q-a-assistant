from pydantic import BaseModel, Field
from typing import Any, Literal, Optional


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Stable user identifier")
    message: str


class ToolCall(BaseModel):
    action: str
    input: dict[str, Any]


class RoutingDecision(BaseModel):
    kind: Literal["tool", "llm"]
    tool: Optional[str] = None
    tool_input: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    answer: str
    used_tool: Optional[str] = None
    tool_latency_ms: Optional[float] = None
    model_latency_ms: Optional[float] = None