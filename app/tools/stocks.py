from typing import Any
import httpx
import yfinance as yf
from ..config import settings


class StocksTool:
    name = "get_stock_price"
    description = "Get latest stock price for a ticker (uses yfinance by default)."
    input_schema = {"ticker": "e.g., AAPL, TSLA"}

    async def run(self, **kwargs) -> str:
        ticker = (kwargs.get("ticker") or "").upper().strip()
        if not ticker:
            return "Please provide a ticker (e.g., AAPL)."

        if settings.STOCKS_PROVIDER == "alphavantage":
            if not settings.ALPHA_VANTAGE_API_KEY:
                return "Alpha Vantage API key missing. Set ALPHA_VANTAGE_API_KEY or use yfinance."
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(
                    "https://www.alphavantage.co/query",
                    params={
                        "function": "GLOBAL_QUOTE",
                        "symbol": ticker,
                        "apikey": settings.ALPHA_VANTAGE_API_KEY,
                    },
                )
                r.raise_for_status()
                data = r.json().get("Global Quote", {})
                price = data.get("05. price")
                if not price:
                    return f"No price found for {ticker}."
                return f"{ticker} last price: {price}"
        else:
            # yfinance path
            t = yf.Ticker(ticker)
            info = t.fast_info
            price = getattr(info, "last_price", None) or info.get("lastPrice") or info.get("last_price")
            if price is None:
                # fallback to history
                hist = t.history(period="1d")
                if hist.empty:
                    return f"No price found for {ticker}."
                price = float(hist["Close"].iloc[-1])
            ccy = info.get("currency", "") if isinstance(info, dict) else getattr(info, "currency", "")
            return f"{ticker} last price: {price} {ccy}"