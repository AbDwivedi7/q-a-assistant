from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .limits import limiter

from ..logging_conf import configure_logging
from ..tools import ToolRegistry, WeatherTool, StocksTool
from ..core.router import Router
from ..core.memory import MemoryStore
from ..core.context import ContextManager

from .routes.chat import router as chat_router
from .routes.health import router as health_router

configure_logging()

def create_app() -> FastAPI:
    app = FastAPI(title="AI Q&A Assistant", version="0.1.0")

    # rate limiting
    app.state.limiter = limiter

    @app.exception_handler(RateLimitExceeded)
    async def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse({"detail": "Rate limit exceeded"}, status_code=429)

    app.add_middleware(SlowAPIMiddleware)

    # CORS (relax for local dev — restrict in prod)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Singletons (registry, memory, context, router) ---
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(StocksTool())

    mem = MemoryStore()          # writes to ./var/data/memory.db
    ctx = ContextManager(mem)
    router = Router(registry, mem, ctx)

    # expose to routes if you need app.state access later
    app.state.registry = registry
    app.state.mem = mem
    app.state.ctx = ctx
    app.state.router = router

    # --- Versioned API routes ---
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(chat_router, prefix="/api/v1")

    # --- Static UI ---
    app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")

    @app.get("/")
    async def root():
        return RedirectResponse(url="/ui/")

    return app

# Uvicorn entrypoint
app = create_app()
