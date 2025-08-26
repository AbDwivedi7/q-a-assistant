import pytest
from app.tools import ToolRegistry, WeatherTool, StocksTool
from app.core.router import Router

@pytest.mark.asyncio
async def test_router_runs():
    reg = ToolRegistry()
    reg.register(WeatherTool())
    reg.register(StocksTool())
    router = Router(reg)

    # We cannot assert deterministic LLM behavior here; just ensure no exception path.
    ans, tool, *_ = await router.route_and_answer("Hello there!")
    assert isinstance(ans, str)