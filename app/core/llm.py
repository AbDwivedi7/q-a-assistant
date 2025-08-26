import json
import time
from typing import Any
from tenacity import retry, stop_after_attempt, wait_exponential
from openai import OpenAI
from .prompts import TOOL_ROUTER_SYSTEM
from ..config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def call_router_llm(user_message: str) -> tuple[dict[str, Any], float]:
    """Return routing JSON dict and model latency."""
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": TOOL_ROUTER_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    txt = resp.choices[0].message.content
    latency_ms = (time.perf_counter() - start) * 1000
    try:
        return json.loads(txt), latency_ms
    except Exception:
        # Fallback: default to direct answer
        return {"type": "final", "answer": txt}, latency_ms


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8))
def call_answer_llm(prompt: str) -> tuple[str, float]:
    start = time.perf_counter()
    resp = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful, concise AI assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    latency_ms = (time.perf_counter() - start) * 1000
    return resp.choices[0].message.content or "", latency_ms