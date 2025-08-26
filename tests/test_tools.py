import pytest
from app.tools import ToolRegistry, WeatherTool, StocksTool

@pytest.mark.asyncio
async def test_registry_and_tools_present():
    reg = ToolRegistry()
    reg.register(WeatherTool())
    reg.register(StocksTool())
    assert reg.get("get_weather") is not None
    assert reg.get("get_stock_price") is not None