import json
import time
from functools import lru_cache
from typing import Optional

try:
    import redis
except Exception:  # pragma: no cover
    redis = None

from ..config import settings


class TTLCache:
    def __init__(self, ttl_seconds: int = 60):
        self.ttl = ttl_seconds
        self.store: dict[str, tuple[float, str]] = {}

    def get(self, key: str) -> Optional[str]:
        itm = self.store.get(key)
        if not itm:
            return None
        ts, val = itm
        if time.time() - ts > self.ttl:
            self.store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: str):
        self.store[key] = (time.time(), value)


_redis = None
if settings.REDIS_URL and redis:
    _redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def cache_get(key: str) -> Optional[str]:
    if _redis:
        return _redis.get(key)
    return _local_cache.get(key)


def cache_set(key: str, value: str, ttl: int = 60):
    if _redis:
        _redis.setex(key, ttl, value)
    else:
        _local_cache.set(key, value)


_local_cache = TTLCache(60)