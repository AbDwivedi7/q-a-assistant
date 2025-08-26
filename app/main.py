from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
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

configure_logging()

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])  # simple reasonable default

app = FastAPI(title="AI Q&A Assistant", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda r, e: (e,))
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
router = Router(registry)
mem = MemoryStore()


@app.post("/chat", response_model=ChatResponse)
@limiter.limit("10/second")
async def chat(req: ChatRequest, _=Depends(enforce_bearer_auth)):
    # Memory: stitch last few turns for context (optional)
    history = mem.last_k(req.user_id, k=6)
    if history:
        prompt = "\n".join([f"{role}: {content}" for role, content in history] + [f"user: {req.message}"])
    else:
        prompt = req.message

    answer, used_tool, tool_latency, model_latency = await router.route_and_answer(prompt)

    mem.add(req.user_id, "user", req.message)
    mem.add(req.user_id, "assistant", answer)

    return ChatResponse(
        answer=answer,
        used_tool=used_tool,
        tool_latency_ms=tool_latency,
        model_latency_ms=model_latency,
    )


@app.get("/health")
async def health():
    return {"status": "ok"}