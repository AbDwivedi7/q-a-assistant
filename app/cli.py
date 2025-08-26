import asyncio
import typer
from app.tools import ToolRegistry, WeatherTool, StocksTool
from app.core.router import Router

cli = typer.Typer()


@cli.command()
def chat():
    """Simple CLI chat loop for the assistant."""
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(StocksTool())
    router = Router(registry)

    async def loop():
        while True:
            try:
                msg = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            ans, tool, *_ = await router.route_and_answer(msg)
            print(f"Bot> {ans} {'(via ' + tool + ')' if tool else ''}")

    asyncio.run(loop())


if __name__ == "__main__":
    cli()