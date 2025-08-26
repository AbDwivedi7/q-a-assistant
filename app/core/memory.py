from __future__ import annotations
from typing import Iterable
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class MemoryStore:
    def __init__(self, url: str = "sqlite:///./memory.db"):
        self.engine: Engine = create_engine(url, future=True)
        with self.engine.begin() as conn:
            conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS messages (user_id TEXT, role TEXT, content TEXT, ts DATETIME DEFAULT CURRENT_TIMESTAMP)"
                )
            )

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