<!-- # Design (≤ 2 pages)

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
- **UI**: Add a lightweight web client with chat UX and streaming. -->


Design Document
===============

Overview
--------

An AI-powered Q&A assistant that (1) answers general knowledge via an LLM and (2) invokes **tools** for real-time/domain data (weather, stock prices). The system is demo-ready but includes clear hooks for enterprise scale (observability, security, extensibility).

> **Note:** This build uses **LLM-only routing** (no hybrid rules engine). The router LLM decides whether to call a tool or answer directly, returning a strict JSON decision.

Architecture (MVP → Enterprise-Ready)
-------------------------------------

**Transport:** FastAPI exposes /chat and /health (optionally versioned as /api/v1/...).**Routing (LLM-only):** A compact **router prompt** enumerates tools and decision rules, and the model replies in JSON:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {"type":"tool","action":"get_weather","input":{"location":"London"}}   `

or

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   {"type":"final","answer":"..."}   `

**Tools (pluggable):**

*   get\_weather(location) → Open-Meteo geocoding + current weather (temperature, wind).
    
*   get\_stock\_price(ticker) → yfinance (or Alpha Vantage if configured).
    

**Answer Composer:** After a tool runs, a short **answer prompt** turns the raw tool string into a concise, on-topic reply with strict guardrails (“answer only what was asked; don’t invent data”).

**Memory (MVP):**

*   **Transcript store** (SQLite) for audit/evaluation.
    
*   No routing logic depends on memory in this build; follow-ups are handled by the LLM router itself.
    

**UI:** Minimal web client (and a CLI) for quick testing/demos.**Security:** Optional bearer token + per-route rate limits.**Observability:** Structured logs; hooks for metrics/tracing.**Evaluation:** YAML-driven router tests, plus optional answer substring checks.

Data Flow
---------

1.  Client → /chat with {user\_id, message}.
    
2.  **LLM Router** decides: tool vs final.
    
3.  If tool, execute the tool asynchronously, then **compose** final answer via answer prompt.
    
4.  Persist minimal transcript (for debugging/eval).
    

Prompt Engineering
------------------

**Router Prompt (strict JSON):**

*   Lists available tools and crisp rules (weather facets; stock price phrasing).
    
*   Includes **negative examples** (e.g., “Apple the fruit” ≠ stock).
    
*   Uses temperature=0 and response\_format={"type":"json\_object"} to reduce variance.
    

**Answer Prompt (guardrails):**

> “Answer **only** what was asked; if the user asks for wind, report wind; keep it concise; do not invent data.”

**Context discipline:** Only the **latest user message** is passed to the router; tool outputs are passed to the answer prompt with the original user ask.

Evaluation (Accuracy & Quality)
-------------------------------

**What we measure**

*   **Routing accuracy:** Predicted action vs. expected (get\_weather, get\_stock\_price, or none).
    
*   **Answer check (optional):** If a test case has expect\_contains, we run the full path (tool + composer) and assert the substring.
    

**How to run**

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   python -m app.core.evaluation evaluator/testcases.yaml   `

Example cases:

Plain textANTLR4BashCC#CSSCoffeeScriptCMakeDartDjangoDockerEJSErlangGitGoGraphQLGroovyHTMLJavaJavaScriptJSONJSXKotlinLaTeXLessLuaMakefileMarkdownMATLABMarkupObjective-CPerlPHPPowerShell.propertiesProtocol BuffersPythonRRubySass (Sass)Sass (Scss)SchemeSQLShellSwiftSVGTSXTypeScriptWebAssemblyYAMLXML`   - id: weather_1    question: What's the weather in London right now?    expect_action: get_weather  - id: stock_1    question: price of AAPL today?    expect_action: get_stock_price  - id: general_1    question: Who wrote Pride and Prejudice?    expect_action: none    expect_contains: Jane Austen   `

Code Quality
------------

*   **Separation of concerns**
    
    *   api/ (optional): HTTP routing, limits, CORS, versioning.
        
    *   core/: router/LLM/prompts/eval/memory.
        
    *   tools/: implementations (weather.py, stocks.py) + registry.
        
    *   models/: transport schemas (Pydantic).
        
*   **Testability:** Singletons are centralized; easy to stub in tests.
    
*   **Hygiene:** .gitignore, .dockerignore, structured logs, Dockerfile, and docker-compose.yml.
    

Scalability (Latency, Security, Extensibility, Observability)
-------------------------------------------------------------

**Latency & Efficiency**

*   Fully **async I/O** tools.
    
*   **Caching**: TTL cache (or Redis) for geocoding, recent tickers, and **router decisions** (keyed by message hash).
    
*   **Model Tiering** (when needed): small model for routing, larger model for final composition.
    
*   **Streaming** to UI for perceived latency gains.
    

**Security & Governance**

*   **Auth**: Bearer token locally; move to JWT/OIDC at the gateway in prod.
    
*   **Rate limiting**: slowapi (global + per-route).
    
*   **Secrets**: environment/secret manager (no keys in code).
    
*   **PII**: redact from logs; configurable retention.
    

**Extensibility**

*   Add a tool by implementing run(\*\*kwargs) and registering it.
    
*   Update the router prompt’s tool list and examples; no code churn in the router.
    

**Observability**

*   **Structured logs**: request id, user id, router decision, tool used, latencies.
    
*   **Metrics** (Prometheus): counters (tool\_calls\_total{tool=...}), histograms (\*\_latency\_ms).
    
*   **Tracing** (OpenTelemetry): spans around route\_llm → tool\_run → answer\_llm.
    

Thought Process: Quick Prototype vs. Enterprise Approach
--------------------------------------------------------

### Quick Prototype (optimize for speed to demo)

*   **LLM-only router**: fastest to build, minimal logic, fewer moving parts.
    
*   Two tools (weather, stocks), no multi-tool planning.
    
*   Minimal persistence (SQLite transcripts), permissive CORS, optional bearer auth.
    
*   Goal: Prove that the system picks tools correctly and produces focused answers.
    

### Enterprise Approach (optimize for scale & reliability)

*   **Versioned API** (/api/v1/...), DI for stubbing in tests, infra as code (Helm/Terraform).
    
*   **Shared state** (Redis/Postgres) and **vector search** for RAG.
    
*   **Model tiering** + decision caching to control cost/latency.
    
*   **Observability stack** (Prometheus + OTel + Grafana).
    
*   **Security**: JWT/OIDC, per-tenant quotas, vault-managed secrets, audits.
    
*   **Lifecycle**: shadow traffic, offline eval, prompt/model change governance.
    

Trade-offs Considered
---------------------

| Dimension | Option A | Option B | Decision & Rationale |

| ----------------- | ---------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ |

| \*\*Routing\*\* | Rules/Hybrid (fast, deterministic) | \*\*LLM-only\*\* (flexible, high recall) | \*\*LLM-only for MVP.\*\* Simpler, covers long tail; fewer systems to maintain. Add caching/tiering later to control latency/cost. |

| \*\*Memory use\*\* | Scoped slots per tool | \*\*No routing dependency\*\* | \*\*No dependency\*\* in MVP; fewer edge cases. Router LLM handles follow-ups; memory kept for audits/eval only. |

| \*\*Answering\*\* | Tool output verbatim | \*\*LLM composer\*\* | \*\*Composer.\*\* Keeps replies concise and on-facet; guardrails reduce hallucination risk. |

| \*\*Freshness\*\* | LLM knowledge only | \*\*External tools\*\* | \*\*Tools\*\* for determinism and real-time data; LLM for language and tone. |

| \*\*Latency/Cost\*\* | One large model for all | \*\*Tiered models + cache\*\* | Start with one model; add tiering & router-decision cache as traffic grows. |

| \*\*State\*\* | SQLite | \*\*Managed DB/Redis\*\* | Start with SQLite (zero-ops); migrate to Redis/Postgres for HA/scale when needed. |

| \*\*Observability\*\* | Basic logs | \*\*Metrics + Tracing\*\* | Add Prometheus/OTel tracing as traffic grows; essential for SLOs and debugging. |

| \*\*Scope\*\* | Multi-location comparisons now | \*\*Defer\*\* | Defer to keep MVP simple and predictable. |

What to Review Against the Rubric
---------------------------------

*   **Functionality:** Weather & stock queries go through tools; general Qs answered directly; answers are focused and factual.
    
*   **Code Quality:** Clear layering (api/ optional, core/, tools/, models/), tests, linting, Docker; secrets externalized.
    
*   **Prompt Engineering:** Router prompt is strict-JSON with examples (incl. negatives); answer prompt enforces concision and non-invention.
    
*   **Scalability Thinking:** Concrete plan for caching, tiering, RAG, observability, auth, and extensibility—each with an MVP→Enterprise path.