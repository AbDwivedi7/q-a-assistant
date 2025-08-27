from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from ..logging_conf import configure_logging
from ..tools import ToolRegistry, WeatherTool, StocksTool
from ..core.router import Router
from ..core.memory import MemoryStore
from ..core.context import ContextManager
from .routes.chat import router as chat_router
from .routes.health import router as health_router
from .limits import limiter  # shared limiter instance

configure_logging()

def create_app() -> FastAPI:
    app = FastAPI(title="AI Q&A Assistant", version="0.1.0")

    # SlowAPI setup
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

    mem = MemoryStore()
    ctx = ContextManager(mem)

    # Router signature in your current code expects (registry, mem, ctx)
    router = Router(registry, mem, ctx)

    # expose to routes
    app.state.registry = registry
    app.state.mem = mem
    app.state.ctx = ctx
    app.state.router = router

    # --- Routes & static files ---
    app.include_router(chat_router)
    app.include_router(health_router)
    app.mount("/ui", StaticFiles(directory="web", html=True), name="ui")

    @app.get("/")
    async def root():
        return RedirectResponse(url="/ui/")

    return app

# Uvicorn entrypoint
app = create_app()
