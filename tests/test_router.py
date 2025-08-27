import pytest
from app.tools import ToolRegistry, WeatherTool, StocksTool
from app.core.router import Router
from app.core.memory import MemoryStore
from app.core.context import ContextManager

@pytest.mark.asyncio
async def test_router_runs():
    reg = ToolRegistry()
    reg.register(WeatherTool())
    reg.register(StocksTool())
    mem = MemoryStore()          # writes to ./var/data/memory.db
    ctx = ContextManager(mem)
    router = Router(reg, mem, ctx)

    # We cannot assert deterministic LLM behavior here; just ensure no exception path.
    ans, tool, *_ = await router.route_and_answer("demo","Hello there!")
    assert isinstance(ans, str)