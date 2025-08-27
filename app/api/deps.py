from __future__ import annotations
from ..tools import ToolRegistry, WeatherTool, StocksTool
from ..core.memory import MemoryStore
from ..core.context import ContextManager
from ..core.router import Router

# Singletons for the process (tests can override these via FastAPI dependency_overrides)
_registry = ToolRegistry()
_registry.register(WeatherTool())
_registry.register(StocksTool())

_mem = MemoryStore()            # now writes to ./var/data/memory.db by default
_ctx = ContextManager(_mem)

# Your Router currently expects (registry, mem, ctx)
_router = Router(_registry, _mem, _ctx)

def get_registry() -> ToolRegistry:
    return _registry

def get_memory() -> MemoryStore:
    return _mem

def get_context() -> ContextManager:
    return _ctx

def get_router() -> Router:
    return _router
