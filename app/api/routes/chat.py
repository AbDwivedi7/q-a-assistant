from fastapi import APIRouter, Depends, Request  # <-- add Request
from ...models.schemas import ChatRequest, ChatResponse
from ...security import enforce_bearer_auth
from ..limits import limiter
from ..deps import get_router, get_memory, get_context

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/second")
async def chat(
    request: Request,  # <-- REQUIRED by slowapi limiter
    req: ChatRequest,
    core_router = Depends(get_router),
    mem = Depends(get_memory),
    ctx = Depends(get_context),
    _ = Depends(enforce_bearer_auth),
):
    # index the user message for semantic recall
    ctx.index_message(req.user_id, "user", req.message)

    # route & answer (hybrid router signature expects user_id + text)
    answer, used_tool, tool_latency, model_latency = await core_router.route_and_answer(
        req.user_id, req.message
    )

    # persist transcript + index assistant reply
    mem.add(req.user_id, "user", req.message)
    mem.add(req.user_id, "assistant", answer)
    ctx.index_message(req.user_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        used_tool=used_tool,
        tool_latency_ms=tool_latency,
        model_latency_ms=model_latency,
    )
