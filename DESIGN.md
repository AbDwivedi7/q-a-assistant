# Design (≤ 2 pages)

## 1) MVP (Quick Prototype)

**Architecture**: A thin FastAPI server exposes `/chat`. A router prompt (ReAct-lite) decides whether to call a tool or answer directly. Tools are Python classes with a uniform `run(**kwargs)` coroutine. The LLM is invoked twice at most: once to route (JSON-only) and optionally once to rewrite the tool output into a friendly answer.

**Why this works**: Fast to build, easy to demo. Decisions are explainable (routing JSON), and tools are simple to add.

## 2) Scaling to Enterprise

### Latency & Efficiency
- **Parallelism**: For multi-tool candidates, fire **speculative async calls**; confirm with LLM which to keep.
- **Caching**: Layered cache (in-memory, Redis) for: geocoding results, recent tickers, and LLM responses (fingerprinted by prompt+inputs).
- **RAG**: For knowledge-heavy queries, add retrieval using a vector DB (FAISS/PGVector/Weaviate). Stream only top-k snippets to the LLM.
- **Compression**: Use short system prompts and structured outputs (JSON) to reduce token usage.
- **Model tiering**: Route to small models for classification/routing; reserve larger models for final answers.
- **Streaming**: Stream partial tokens to the client for perceived latency improvement.

### Security & Access Control
- **API Gateway**: JWT verification, IP allowlists, DDoS protection, **rate limiting** per tenant.
- **Secret Management**: Rotate keys via a vault (AWS Secrets Manager, Hashicorp Vault). No secrets in code.
- **Data Governance**: PII redaction before logging; configurable data retention.
- **Tenant Isolation**: Namespace caches/stores by tenant; use separate queues or projects for regulated customers.

### Extensibility
- **Tool Interface**: Each tool declares `name`, `description`, `input_schema`, `run`. Register in a `ToolRegistry`. Hot-pluggable via entry points.
- **Contracts**: JSON Schema for tool inputs/outputs enables validation and UI generation.
- **Multiple Backends**: Tools can wrap REST, gRPC, or DB queries; router prompt is updated automatically (or use function calling).

### Observability & Logging
- **Structured Logs**: Request IDs, user IDs, tool timings, model latencies.
- **Metrics**: Prometheus counters for tool calls, error rates, p50/p95 latencies, token usage.
- **Tracing**: OpenTelemetry spans around: routing LLM → tool call → answer LLM. Export to Grafana Tempo/Jaeger.
- **Replay**: Store anonymized conversations; replay with new models for regression testing.

### Evaluation (Accuracy & Quality)
- **Routing Accuracy**: YAML test cases → check predicted action vs expected.
- **Tool Correctness**: Golden outputs for deterministic tools; tolerance windows for prices/temps.
- **Answer Quality**: LLM-as-judge with calibrated rubric; human sampling for high-stakes domains.
- **Continuous Evaluation**: Nightly CI job; fail builds on significant regressions. Track win/loss vs baseline.

## 3) Trade-offs
- **LLM-Only vs Tooling**: Tools add complexity but provide freshness & determinism. We keep them optional for local runs.
- **Router Heuristics vs LLM**: Heuristics are cheap but brittle; we use a small LLM for routing with JSON output, plus tests.
- **Speed vs Cost**: Model tiering & caching balance cost while preserving quality.
- **Simplicity vs Observability**: Added infra (metrics, tracing) increases ops overhead; justified for enterprise.

## 4) Future Work
- **Policy & Guardrails**: Add content filters and sensitive-data classifiers.
- **Multi-turn Tool Plans**: Support multi-step toolchains via planning models or workflow engines.
- **Memory**: Switch SQLite to a vectorized long-term memory store with recency + semantic mixing.
- **UI**: Add a lightweight web client with chat UX and streaming.
