import asyncio
import typer
from typing import List
from app.tools import ToolRegistry, WeatherTool, StocksTool
from app.core.router import Router
from app.core.memory import MemoryStore
from app.core.context import ContextManager

cli = typer.Typer(help="CLI for the AI Q&A assistant")

@cli.command()
def chat(
    message: List[str] = typer.Argument(
        None,
        help="Optional one-shot question. If omitted, starts interactive mode.",
        show_default=False,
    ),
    user: str = typer.Option("cli", "--user", "-u", help="User id label"),
):
    """
    Chat with the assistant.

    Examples:
      python -m app.cli chat
      python -m app.cli chat what is the weather in bangalore
      python -m app.cli chat -u demo price of AAPL
    """
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(StocksTool())
    mem = MemoryStore()
    ctx = ContextManager(mem)
    router = Router(registry, mem, ctx)

    async def ask_once(text: str):
        ans, tool, *_ = await router.route_and_answer(user, text)
        print(f"Bot> {ans} {'(via ' + tool + ')' if tool else ''}")

    if message:
        text = " ".join(message).strip()
        if not text:
            raise typer.Exit(code=1)
        asyncio.run(ask_once(text))
        return

    async def loop():
        while True:
            try:
                msg = input("You> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not msg:
                continue
            await ask_once(msg)

    asyncio.run(loop())

if __name__ == "__main__":
    cli()
