# AI Q&A Assistant (Tools + LLM)

A production-quality starter that routes between an LLM and real APIs (tools). Includes:

- **FastAPI** service with `/chat` endpoint
- **Two tools**: weather (Open-Meteo) and stock prices (yfinance / Alpha Vantage)
- **Router prompt** that decides when to call tools
- **Optional memory** (SQLite) across turns
- **Evaluation harness** for routing accuracy
- **Caching & rate limits**, **logging**, **Docker** support

## Quickstart

### 1) Setup
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your keys (OPENAI_API_KEY at minimum)
```

### 2) Run the API
```bash
uvicorn app.main:app --reload --port 8000
```

### 3) Call the API
```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer change-me' \
  -d '{"user_id":"demo","message":"What\'s the weather in Paris?"}'
```

### 4) UI Interface to chat
```bash
http://localhost:8000/
```

### 5) CLI mode
```bash
python -m app.cli chat
```
```bash
python -m app.cli chat what is the weather in london
```
```bash
python -m app.cli chat -u Abhishek price of AAPL
```

### 6) Evaluation
Run the simple router eval:
```
python -m app.core.evaluation evaluator/testcases.yaml
```

## Project Structure
```
app/
  core/           # context, evaluation, llm, memory, prompts, retrieval, router 
  models/         # request/response schemas
  tools/          # tool implementations + registry
  config.py       # config required like apenai api key, stock provider, weather api endpoints etc
  logging.py      # logging
  main.py         # FastAPI app
  cli.py          # CLI interface
  security.py     # Authorization for the API Endpoints

web/
  app.js          # Javascript file for the Web UI
  index.html      # HTML file for the Web UI
  style.css       # Stylesheet file for the Web UI
```

## Add a New Tool
Create `app/tools/my_tool.py`:
```python
class MyTool:
  name = "get_custom"
  description = "Describe what it does"
  input_schema = {"param": "description"}
  async def run(self, **kwargs) -> str:
      # fetch or compute
      return "result"
```
Register it in `app/main.py`:
```python
from .tools.my_tool import MyTool
registry.register(MyTool())
```
The router LLM will see tool names/desc from the prompt; update `prompts.py` to mention your new tool and guidance rules.

This returns per-case correctness; extend with more cases and metrics.

## Security & Ops
- **Auth**: Bearer token via `API_AUTH_TOKEN` (optional for local prototyping)
- **Rate limiting**: `slowapi` (60/min default), plus per-route limits
- **CORS**: permissive for demo; scope down in production
- **Logging**: `structlog` configured in `logging_conf.py`
- **Healthcheck**: `/health`

## Environment Vars
See `.env.example` and `app/config.py`. Use Redis by setting `REDIS_URL` for shared cache in multi-replica deployments.

## Notes
- The FAISS example uses a toy embedding to avoid API dependencies. Replace with a real embedding model for production RAG.
- Stock data via yfinance can be slow or rate-limited; for enterprise use Alpha Vantage or a paid market data provider.
