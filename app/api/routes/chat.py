from fastapi import APIRouter, Depends, Request

from ...models.schemas import ChatRequest, ChatResponse
from ...security import enforce_bearer_auth
from ..limits import limiter

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("10/second")
async def chat(request: Request, req: ChatRequest, _=Depends(enforce_bearer_auth)):
    """
    Chat endpoint that:
      - indexes the user message in ContextManager
      - routes (rules/LLM) and executes tools
      - persists transcript to MemoryStore
      - indexes assistant reply in ContextManager
    """
    latest = req.message

    # Singletons prepared in app.api.server:create_app()
    mem = request.app.state.mem
    ctx = request.app.state.ctx
    core_router = request.app.state.router

    # index the user message for semantic recall
    ctx.index_message(req.user_id, "user", latest)

    # route & answer (hybrid router signature expects user_id + text)
    answer, used_tool, tool_latency, model_latency = await core_router.route_and_answer(req.user_id, latest)

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
