from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Depends, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .models.schemas import ChatRequest, ChatResponse
from .security import enforce_bearer_auth
from .logging_conf import configure_logging
from .tools import ToolRegistry, WeatherTool, StocksTool
from .core.router import Router
from .core.memory import MemoryStore
from .core.context import ContextManager

configure_logging()

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])  # simple reasonable default

app = FastAPI(title="AI Q&A Assistant", version="0.1.0")
app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded)
async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global singletons
registry = ToolRegistry()
registry.register(WeatherTool())
registry.register(StocksTool())
# router = Router(registry)
mem = MemoryStore()
ctx = ContextManager(mem)
router = Router(registry, mem, ctx)


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/second")
async def chat(request: Request, req: ChatRequest, _=Depends(enforce_bearer_auth)):
    latest = req.message
    
    # index the user message for semantic recall
    ctx.index_message(req.user_id, "user", latest)

    answer, used_tool, tool_latency, model_latency = await router.route_and_answer(req.user_id, latest)

    # persist transcript + index assistant reply
    mem.add(req.user_id, "user", req.message)
    mem.add(req.user_id, "assistant", answer)
    ctx.index_message(req.user_id, "assistant", answer)

    return ChatResponse(answer=answer, used_tool=used_tool, tool_latency_ms=tool_latency, model_latency_ms=model_latency)


@app.get("/health")
async def health():
    return {"status": "ok"}