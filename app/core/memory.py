# app/core/memory.py
from __future__ import annotations
from typing import Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

class MemoryStore:
    def __init__(self, url: str = "sqlite:///./memory.db"):
        self.engine: Engine = create_engine(url, future=True)
        with self.engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS messages (user_id TEXT, role TEXT, content TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP)"
            ))
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS kv (user_id TEXT, namespace TEXT, key TEXT, value TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP)"
            ))

    def add(self, user_id: str, role: str, content: str):
        with self.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO messages (user_id, role, content) VALUES (:u, :r, :c)"),
                {"u": user_id, "r": role, "c": content},
            )

    def last_k(self, user_id: str, k: int = 6) -> list[tuple[str, str]]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                text("SELECT role, content FROM messages WHERE user_id=:u ORDER BY ts DESC LIMIT :k"),
                {"u": user_id, "k": k},
            ).all()
        return [(r[0], r[1]) for r in reversed(rows)]

    # Scoped KV for tool parameters and metadata (namespaces = tool names or "meta")
    def set_kv(self, user_id: str, namespace: str, key: str, value: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                text("INSERT INTO kv (user_id, namespace, key, value) VALUES (:u, :n, :k, :v)"),
                {"u": user_id, "n": namespace, "k": key, "v": value},
            )

    def get_kv(self, user_id: str, namespace: str, key: str, max_age_minutes: Optional[int] = 24 * 60) -> Optional[str]:
        with self.engine.begin() as conn:
            if max_age_minutes is None:
                row = conn.execute(
                    text("SELECT value FROM kv WHERE user_id=:u AND namespace=:n AND key=:k ORDER BY ts DESC LIMIT 1"),
                    {"u": user_id, "n": namespace, "k": key},
                ).fetchone()
            else:
                row = conn.execute(
                    text("SELECT value FROM kv WHERE user_id=:u AND namespace=:n AND key=:k AND ts >= datetime('now', :window) ORDER BY ts DESC LIMIT 1"),
                    {"u": user_id, "n": namespace, "k": key, "window": f"- {max_age_minutes} minutes"},
                ).fetchone()
        return row[0] if row else None
