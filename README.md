
# AI Q&A Assistant (Tools + LLM)

A production-quality starter that routes between an LLM and real APIs (tools). Includes:

*   **FastAPI** service with `/chat` endpoint
    
*   **Two tools**: weather (Open-Meteo) and stock prices (yfinance / Alpha Vantage)
    
*   **Router prompt** that decides when to call tools
    
*   **Optional memory** (SQLite) across turns
    
*   **Evaluation harness** for routing accuracy
    
*   **Caching & rate limits**, **logging**, **Docker** support
    

> **Requirements**
> 
> *   Python **3.10+**
>     
> *   An **OpenAI API key** (`OPENAI_API_KEY`)
>     
> *   (Optional) **Alpha Vantage** key if using that stock provider
>     
> *   (Optional) **Redis** if you enable external caching
>     

## Quickstart

### 1) Setup

`python -m venv .venv && source .venv/bin/activate pip install -r requirements.txt cp .env.example .env # Edit .env with your keys (OPENAI_API_KEY at minimum)`

Common env vars (see full list below):

*   `OPENAI_API_KEY` (required)
    
*   `API_AUTH_TOKEN` (optional for local; if set, you must send a Bearer token)
    

### 2) Run the API

`uvicorn app.main:app --reload --port 8000`

### 3) Call the API

`curl -X POST http://localhost:8000/api/v1/chat \   -H 'Content-Type: application/json' \   -H 'Authorization: Bearer change-me' \   -d '{"user_id":"demo","message":"What'\''s the weather in Paris?"}'`

### 4) UI Interface to chat

`http://localhost:8000/`

*   The web client posts to **`/chat`** and shows tool/model latencies.
    
*   You can save the Bearer token and user id in the UI header.
    

### 5) CLI mode

`python -m app.cli chat`

`python -m app.cli chat what is the weather in london`

`python -m app.cli chat -u Abhishek price of AAPL`

### 6) Evaluation

Run the simple router eval:

`python -m app.core.evaluation evaluator/testcases.yaml`

This prints per-case results plus a summary/JSON block you can use in CI.

* * *

## Project Structure

```
app/
  api/
    routes/       # FastAPI routers (chat.py, health.py, etc.)
    deps.py       # dependency providers (router, memory, context, registry)
    limits.py     # shared slowapi Limiter instance
    server.py     # app factory + API versioning + static UI mount
  core/           # context, evaluation, llm, memory, prompts, retrieval, router 
  models/         # request/response schemas
  tools/          # tool implementations + registry
  config.py       # config (OpenAI key, stock provider, weather endpoints, etc.)
  logging_conf.py # logging setup
  main.py         # thin entrypoint: `from .api.server import app`
  cli.py          # CLI interface
  security.py     # Authorization for the API endpoints

web/
  app.js          # JavaScript for the Web UI
  index.html      # HTML for the Web UI
  styles.css      # Stylesheet for the Web UI
```

> ℹ️ Note: the actual stylesheet file is `styles.css` in some branches; if your build references `styles.css`, ensure the filename in `/web` matches or update the `<link>` in `index.html`.

* * *

## Add a New Tool

Create `app/tools/my_tool.py`:

```
class MyTool:
  name = "get_custom"
  description = "Describe what it does"
  input_schema = {"param": "description"}

  async def run(self, **kwargs) -> str:
    # fetch or compute  return "result"
```

Register it in `app/main.py`:

`from .tools.my_tool import MyTool registry.register(MyTool())`

The router LLM will see tool names/desc from the prompt; update `prompts.py` to mention your new tool and guidance rules.

This returns per-case correctness; extend with more cases and metrics.

* * *

## API Reference

### `POST /api/v1/chat`

**Request**

`{   "user_id": "demo",   "message": "What's the weather in Paris?" }`

**Response**

`{   "answer": "Current weather at Paris: 24.1°C, wind 10.7 km/h.",   "used_tool": "get_weather",   "tool_latency_ms": 0.0,   "model_latency_ms": 965.3 }`

**Headers**

*   Optional: `Authorization: Bearer <API_AUTH_TOKEN>` (if you set it in `.env`)
    

### `GET /api/v1/health`

`curl http://localhost:8000/api/v1/health # => {"status":"ok"}`

### Docs

*   FastAPI docs are available at **`/docs`** (Swagger UI) and **`/redoc`**.
    

* * *

## Environment Variables

(Defined in `.env.example` and `app/config.py`)

| Var | Purpose | Required | Example |
| --- | --- | --- | --- |
| OPENAI_API_KEY | LLM access | Yes | sk-... |
| OPENAI_MODEL | Model name for router/answers | No | gpt-4o-mini |
| WEATHER_API_BASE | Weather API base URL | No | https://api.open-meteo.com/v1/forecast |
| STOCKS_PROVIDER | Stock data backend | No | yfinance or alphavantage |
| ALPHA_VANTAGE_API_KEY | If using Alpha Vantage | If STOCKS_PROVIDER=alphavantage | ... |
| REDIS_URL | Optional external cache | No | redis://localhost:6379/0 |
| API_AUTH_TOKEN | Bearer token for API | No (recommended in prod) | change-me |
| LOG_LEVEL | Logging level | No | INFO |

* * *

## Docker

Build & run:

`docker build -t ai-qa-assistant:latest . docker run -p 8000:8000 --env-file .env ai-qa-assistant:latest`

Compose (includes Redis):

`docker-compose up --build`

* * *

## Tests & Linting

Run tests:

`pytest -q`

Format & lint:

`ruff check --fix . black .`

(Optionally set up `pre-commit` to enforce these locally.)

* * *

## Security & Ops

*   **Auth**: Bearer token via `API_AUTH_TOKEN` (optional for local prototyping)
    
*   **Rate limiting**: `slowapi` (60/min default), plus per-route limits
    
*   **CORS**: permissive for demo; scope down in production
    
*   **Logging**: `structlog` configured in `logging_conf.py`
    
*   **Healthcheck**: `/health`
    
*   **Secrets**: never commit `.env`; use a secrets manager in production
    

* * *

## Troubleshooting

*   **`ModuleNotFoundError: pydantic_settings`**  
    Run: `pip install -r requirements.txt` (ensure your venv is active).
    
*   **`OPENAI_API_KEY Field required` / 401 from OpenAI**  
    Set `OPENAI_API_KEY` in `.env` and reload your server/session.
    
*   **Rate limit decorator error (`No "request" argument`)**  
    Ensure the FastAPI handler includes `request: Request` **when** using `@limiter.limit(...)` from `slowapi`.
    
*   **`__pycache__` files show up in Git**  
    They are likely already tracked. Run:  
    `git rm -r --cached **/__pycache__` then commit. `.gitignore` already ignores them.
    
*   **Stocks via yfinance are slow/rate-limited**  
    Switch to `STOCKS_PROVIDER=alphavantage` and set `ALPHA_VANTAGE_API_KEY`, or use a paid data provider.
    

* * *

## Notes

*   The FAISS example uses a toy embedding to avoid API dependencies. Replace with a real embedding model for production RAG.
    
*   Stock data via yfinance can be slow or rate-limited; for enterprise use Alpha Vantage or a paid market data provider.